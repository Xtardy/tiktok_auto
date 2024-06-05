import os
import random
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# Chemin des dossiers
input_path = 'output_videos_with_subtitles'
output_path = 'output_videos_with_music'
background_music_path = 'background_music'

# Intensité de la musique de fond (entre 0 et 1)
background_music_volume = 0.2

# Obtenir la liste des fichiers vidéo générés
generated_videos = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith(('.mp4', '.avi', '.mov'))]

# Obtenir la liste des fichiers de musique de fond
background_music_files = [os.path.join(background_music_path, f) for f in os.listdir(background_music_path) if f.endswith(('.mp3', '.wav', '.ogg'))]

# Créer le dossier de sortie s'il n'existe pas
os.makedirs(output_path, exist_ok=True)

for video_file in generated_videos:
    # Charger la vidéo
    video_clip = VideoFileClip(video_file)
    
    # Choisir aléatoirement une musique de fond
    background_music_file = random.choice(background_music_files)
    background_music = AudioFileClip(background_music_file).volumex(background_music_volume)
    
    # Tronquer la musique de fond si elle est plus longue que la vidéo
    if background_music.duration > video_clip.duration:
        background_music = background_music.subclip(0, video_clip.duration)
    
    # Ajuster la durée de la musique de fond à la durée de la vidéo (si plus courte, elle boucle)
    background_music = background_music.set_duration(video_clip.duration)
    
    # Créer un composite audio en ajoutant la musique de fond au son original de la vidéo
    final_audio = CompositeAudioClip([video_clip.audio, background_music])
    
    # Assigner le composite audio à la vidéo
    final_clip = video_clip.set_audio(final_audio)
    
    # Sauvegarder la vidéo finale avec la musique de fond ajoutée
    output_filename = os.path.join(output_path, os.path.basename(video_file))
    final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')

print("Ajout de la musique de fond terminé!")
