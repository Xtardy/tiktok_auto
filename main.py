from download_video import download_video, download_subtitles
from cut_video import cut_video, find_cut_points, adjust_cut_points
import moviepy.editor as mp
import os

links_file = 'links/links.txt'
output_dir = 'downloaded_videos'
proxy = 'http://cache.univ-st-etienne.fr:3128'

# Create the output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Read links from the file
with open(links_file, 'r') as file:
    links = file.readlines()

# Download each video
for link in links:
    url = link.strip()
    if url:
        download_video(url, output_dir, proxy)
    
video_path = "downloaded_videos/test.mp4"
audio_path = "audio.wav"
output_dir = "video_segments"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Extraire l'audio de la vidéo
video = mp.VideoFileClip(video_path)
video.audio.write_audiofile(audio_path)

# Trouver les points de coupure basés sur l'audio
cut_points = find_cut_points(audio_path)

# Ajuster les points de coupure pour des segments de plus d'une minute
adjusted_cut_points = adjust_cut_points(cut_points)

# Couper la vidéo en utilisant les points de coupure ajustés
cut_video(video_path, adjusted_cut_points, output_dir)

# Supprimer le fichier audio temporaire
os.remove(audio_path)


