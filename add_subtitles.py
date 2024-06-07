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
    
    # Supprimer le fichier audio temporaire
    os.remove(audio_path)

    return transcription

def generate_srt_from_transcription(transcription, srt_path, duration, threshold = 1):
    words = transcription.split()
    num_words = len(words)

    if num_words == 0:
        raise ValueError("La transcription est vide, aucun mot détecté.")
    
    word_duration = duration / num_words
    
    subtitles = []
    current_phrase = []
    current_start_time = None
    last_end_time = None
    
    for i, word in enumerate(words):
        start_time = timedelta(seconds=i * word_duration)
        end_time = timedelta(seconds=(i + 1) * word_duration)
        
        if last_end_time is None or (start_time - last_end_time) <= timedelta(seconds=threshold):
            if not current_phrase:
                current_start_time = start_time
            current_phrase.append(word)
        else:
            if current_phrase:
                subtitles.append(srt.Subtitle(
                    index=len(subtitles) + 1,
                    start=current_start_time,
                    end=last_end_time,
                    content=' '.join(current_phrase),
                ))
            current_phrase = [word]
            current_start_time = start_time
        
        last_end_time = end_time
    
    if current_phrase:
        subtitles.append(srt.Subtitle(
            index=len(subtitles) + 1,
            start=current_start_time,
            end=last_end_time,
            content=' '.join(current_phrase),
        ))
    
    srt_content = srt.compose(subtitles)
    with open(srt_path, "w", encoding="utf-8") as file:
        file.write(srt_content)

def generate_subtitle_image(text, video_size):
    # Créer une image avec un fond transparent
    img = Image.new('RGBA', video_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Utiliser une police de caractères
    font_path = "arial.ttf"  # Assurez-vous que le chemin est correct
    font = ImageFont.truetype(font_path, 38)
    
    # Mesurer la taille du texte et centrer
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (video_size[0] - text_width) // 2
    text_y = video_size[1] - text_height - 100  # Ajuster la position verticale
    
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
            start_time = sub.start.total_seconds()
            end_time = sub.end.total_seconds()
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
        transcription = transcribe_audio_with_wav2vec(video_path)
        srt_path = "output.srt"
        
        # Charger la vidéo pour obtenir la durée
        video_clip = VideoFileClip(video_path)
        duration = video_clip.duration
        
        # Générer le fichier SRT
        generate_srt_from_transcription(transcription, srt_path, duration)
        
        
        # Ajouter les sous-titres à la vidéo
        output_video_path = "video_with_subtitles.mp4"
        add_subtitles_to_video(video_path, srt_path, output_video_path)
        print(f"Processed video saved to {output_video_path}")
    except ValueError as e:
        print(f"Error: {e}")



process_video_subtitles("test.mp4")
