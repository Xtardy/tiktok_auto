
import os
import random
from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip

# Chemins des dossiers
segments_path = 'video_segments'
gameplay_path = 'gameplay_videos'

# Obtenir les listes de fichiers vidéo
segment_videos = [os.path.join(segments_path, f) for f in os.listdir(segments_path) if f.endswith(('.mp4', '.avi', '.mov'))]
gameplay_videos = [os.path.join(gameplay_path, f) for f in os.listdir(gameplay_path) if f.endswith(('.mp4', '.avi', '.mov'))]

# Paramètres
crop_percentage = 0.1  # Pourcentage à recadrer de chaque côté (10% ici)
final_width = 720
final_height = 1280
padding = 10  # Bande noire entre les vidéos

# Fonction pour enlever le son d'un clip
def remove_audio(clip):
    return clip.without_audio()

# Fonction pour recadrer un clip
def crop_clip(clip, crop_percentage):
    width, height = clip.size
    x_crop = int(width * crop_percentage)
    return clip.crop(x1=x_crop, x2=width - x_crop)

# Créer une sortie pour chaque vidéo segment
output_path = 'output_videos'
os.makedirs(output_path, exist_ok=True)

for segment_video in segment_videos:
    # Charger la vidéo segment
    segment_clip = VideoFileClip(segment_video)
    
    # Choisir aléatoirement une vidéo gameplay
    gameplay_video = random.choice(gameplay_videos)
    gameplay_clip = VideoFileClip(gameplay_video)
    
    # Enlever le son de la vidéo gameplay
    gameplay_clip = remove_audio(gameplay_clip)
    
    # Tronquer la vidéo gameplay si elle est plus longue que la vidéo segment
    if gameplay_clip.duration > segment_clip.duration:
        gameplay_clip = gameplay_clip.subclip(0, segment_clip.duration)
    
    # Recadrer les vidéos
    segment_clip = crop_clip(segment_clip, crop_percentage)
    gameplay_clip = crop_clip(gameplay_clip, crop_percentage)
    
    # Ajuster les tailles des vidéos pour qu'elles aient la même largeur
    segment_clip = segment_clip.resize(width=final_width)
    gameplay_clip = gameplay_clip.resize(width=final_width)
    
    # Calculer la hauteur totale avec la bande noire entre les vidéos
    total_height = segment_clip.h + gameplay_clip.h + padding
    
    # Positionner les vidéos
    segment_clip = segment_clip.set_position(("center", "top"))
    gameplay_clip = gameplay_clip.set_position(("center", segment_clip.h + padding))
    
    # Créer une bande noire entre les vidéos
    black_bar = ColorClip(size=(final_width, padding), color=(0, 0, 0)).set_duration(segment_clip.duration)
    
    # Créer une composition vidéo
    final_clip = CompositeVideoClip([segment_clip, black_bar.set_position(("center", segment_clip.h)), gameplay_clip], size=(final_width, total_height))
    
    # Ajouter des bandes noires en haut et en bas si nécessaire
    if total_height < final_height:
        top_black = ColorClip(size=(final_width, (final_height - total_height) // 2), color=(0, 0, 0)).set_duration(segment_clip.duration)
        bottom_black = ColorClip(size=(final_width, (final_height - total_height + 1) // 2), color=(0, 0, 0)).set_duration(segment_clip.duration)
        final_clip = CompositeVideoClip([top_black.set_position(("center", "top")), final_clip.set_position(("center", top_black.h)), bottom_black.set_position(("center", top_black.h + total_height))], size=(final_width, final_height))
    
    # Sauvegarder la vidéo finale
    output_filename = os.path.join(output_path, f"combined_{os.path.basename(segment_video)}")
    final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')

print("Traitement terminé!")
