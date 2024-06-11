import os
import numpy as np
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import srt
from datetime import timedelta
from subtitle_duration import read_srt, segment_transcript, format_subtitles_srt

def read_transcript(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def parse_transcript(transcript):
    segments = []
    lines = transcript.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if '-->' in line:
            times = line.split('-->')
            start_time = float(times[0].strip())
            end_time = float(times[1].strip())
            i += 1
            text_lines = []
            while i < len(lines) and '-->' not in lines[i]:
                text_lines.append(lines[i].strip())
                i += 1
            text = ' '.join(text_lines)
            segments.append({
                'start_time': start_time,
                'end_time': end_time,
                'text': text
            })
        else:
            i += 1
    return segments

def generate_srt_from_segments(segments, srt_path):
    subtitles = []
    for i, segment in enumerate(segments):
        start_time = timedelta(seconds=segment['start_time'])
        end_time = timedelta(seconds=segment['end_time'])
        subtitle = srt.Subtitle(
            index=i + 1,
            start=start_time,
            end=end_time,
            content=segment['text'],
        )
        subtitles.append(subtitle)
    
    srt_content = srt.compose(subtitles)
    with open(srt_path, "w", encoding="utf-8") as file:
        file.write(srt_content)

def generate_subtitle_image(text, video_size):
    # Créer une image avec un fond transparent
    img = Image.new('RGBA', video_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Utiliser la police de caractères AvenirNext
    font_path = "AvenirNext-Regular.ttf"  # Assurez-vous que le chemin est correct
    font = ImageFont.truetype(font_path, 58)
    
    # Mesurer la taille du texte et centrer
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (video_size[0] - text_width) // 2
    text_y = video_size[1] - text_height - 100  # Ajuster la position verticale
    
    # Ajouter un contour noir pour le texte
    outline_range = 4
    for adj in range(-outline_range, outline_range+1):
        draw.text((text_x + adj, text_y), text, font=font, fill="black")
        draw.text((text_x, text_y + adj), text, font=font, fill="black")

    for adj in [(i, j) for i in range(-outline_range, outline_range+1) for j in range(-outline_range, outline_range+1)]:
        draw.text((text_x + adj[0], text_y + adj[1]), text, font=font, fill="black")

    # Ajouter le texte en jaune par-dessus le contour
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

def process_video_subtitles(video_path, transcript_path):
    try:
        # Lire et parser le transcript
        transcript = read_transcript(transcript_path)
        segments = parse_transcript(transcript)
        
        # Générer le fichier SRT
        srt_path = "output.srt"
        generate_srt_from_segments(segments, srt_path)
        
        # Ajouter les sous-titres à la vidéo
        output_video_path = "video_with_subtitles.mp4"
        add_subtitles_to_video(video_path, srt_path, output_video_path)
        print(f"Processed video saved to {output_video_path}")
    except ValueError as e:
        print(f"Error: {e}")

# Exemple d'utilisation
process_video_subtitles("test.mp4", "transcript.txt")
