import os
import librosa
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import moviepy.editor as mp  # Importer moviepy.editor en tant que mp
import numpy as np
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import srt
from datetime import timedelta
from subtitle_duration import read_srt,segment_transcript,format_subtitles_srt



def transcribe_audio_with_wav2vec(video_path):
    # Charger la vidéo et extraire l'audio
    video = mp.VideoFileClip(video_path)
    audio_path = "temp_audio.wav"
    video.audio.write_audiofile(audio_path, codec='pcm_s16le')

    # Charger l'audio
    audio_input, sample_rate = librosa.load(audio_path, sr=16000)
    
    # Charger le modèle Wav2Vec 2.0
    processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
    model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
    
    # processor = Wav2Vec2Processor.from_pretrained("openai/whisper-large-v3")
    # model = Wav2Vec2ForCTC.from_pretrained("openai/whisper-large-v3")


    # Utiliser le GPU si disponible
    device = torch.device("cpu")
    model.to(device)

    # Préparer les entrées pour le modèle
    input_values = processor(audio_input, sampling_rate=16000, return_tensors="pt", padding="longest").input_values.to(device)

    # Effectuer la transcription
    with torch.no_grad():
        logits = model(input_values).logits

    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)[0]

    # Extraire les informations de timing des mots
    word_timestamps = processor.decode(predicted_ids[0], output_word_offsets=True)
    
    # Supprimer le fichier audio temporaire
    os.remove(audio_path)

    return transcription, word_timestamps

def group_words_into_phrases(word_timestamps, max_gap=1.0):
    phrases = []
    current_phrase = []
    current_start_time = word_timestamps['word_offsets'][0]['start_offset']  # Convert to seconds
    for i, word_info in enumerate(word_timestamps['word_offsets']):
        current_phrase.append(word_info['word'])
        if (i == len(word_timestamps['word_offsets']) - 1 or
                (word_timestamps['word_offsets'][i + 1]['start_offset'] - word_info['end_offset'])  > max_gap):
            end_time = word_info['end_offset'] 
            phrases.append({
                'phrase': ' '.join(current_phrase),
                'start_time': current_start_time,
                'end_time': end_time
            })
            if i < len(word_timestamps['word_offsets']) - 1:
                current_phrase = []
                current_start_time = word_timestamps['word_offsets'][i + 1]['start_offset']
    return phrases


def generate_srt_from_phrases(phrases, srt_path):
    subtitles = []
    for i, phrase_info in enumerate(phrases):
        start_time = timedelta(seconds=float(phrase_info['start_time']))
        end_time = timedelta(seconds=float(phrase_info['end_time']))
        subtitle = srt.Subtitle(
            index=i + 1,
            start=start_time,
            end=end_time,
            content=phrase_info['phrase'],
        )
        subtitles.append(subtitle)
    
    srt_content = srt.compose(subtitles)
    with open(srt_path, "w", encoding="utf-8") as file:
        file.write(srt_content)
        
    transcript = read_srt(srt_path)
    subtitles = segment_transcript(transcript)
    srt_content = format_subtitles_srt(subtitles)
    with open(srt_path, "w", encoding="utf-8") as file:
        file.write(srt_content)

def generate_subtitle_image(text, video_size):
    # Créer une image avec un fond transparent
    img = Image.new('RGBA', video_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Utiliser une police de caractères
    font_path = "arial.ttf"  # Assurez-vous que le chemin est correct
    font = ImageFont.truetype(font_path, 46)
    
    # Mesurer la taille du texte et centrer
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (video_size[0] - text_width) // 2
    text_y = video_size[1] - text_height - 700  # Ajuster la position verticale
    
    # Ajouter le texte à l'image
    draw.text((text_x, text_y), text, font=font, fill="yellow")
    
    # Convertir l'image PIL en tableau numpy
    return np.array(img)

def generate_subtitles_from_srt(video_clip, srt_path):
    subtitles = []
    with open(srt_path, 'r', encoding='utf-8') as srt_file:
        srt_content = srt_file.read()
        subs = list(srt.parse(srt_content))
        for sub in subs:
            start_time = sub.start.total_seconds()/60
            end_time = sub.end.total_seconds()/60
            text = sub.content
            
            # Générer l'image de sous-titre
            subtitle_img = generate_subtitle_image(text, video_clip.size)
            subtitle_clip = ImageClip(subtitle_img).set_start(start_time).set_duration(end_time - start_time).set_position(('center', 'bottom'))
            subtitles.append(subtitle_clip)
    return subtitles

def add_subtitles_to_video(video_path, srt_path, output_path):
    video_clip = VideoFileClip(video_path)
    subtitles = generate_subtitles_from_srt(video_clip, srt_path)
    final_clip = CompositeVideoClip([video_clip] + subtitles)
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

def process_video_subtitles(video_path):
    try:
        # Transcrire l'audio avec Wav2Vec 2.0
        transcription, word_timestamps = transcribe_audio_with_wav2vec(video_path)
        srt_path = "output.srt"
        
        # Regrouper les mots en phrases
        phrases = group_words_into_phrases(word_timestamps)
        
        # Générer le fichier SRT
        generate_srt_from_phrases(phrases, srt_path)
        
        # Ajouter les sous-titres à la vidéo
        output_video_path = "video_with_subtitles.mp4"
        add_subtitles_to_video(video_path, srt_path, output_video_path)
        print(f"Processed video saved to {output_video_path}")
    except ValueError as e:
        print(f"Error: {e}")

# Exemple d'utilisation
process_video_subtitles("test.mp4")


