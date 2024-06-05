import os
from pydub import AudioSegment, silence
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import moviepy.editor as mp

# Fonction pour trouver les points de coupure dans l'audio
def find_cut_points(audio_path, min_silence_len=1000, silence_thresh=-40):
    audio = AudioSegment.from_file(audio_path)
    silences = silence.detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    cut_points = [(start + (stop - start) // 2) / 1000 for start, stop in silences]  # Moyenne et conversion en secondes
    return cut_points

# Fonction pour ajuster les points de coupure pour des segments de plus d'une minute
def adjust_cut_points(cut_points, min_segment_length=60):
    adjusted_cut_points = []
    last_cut_point = 0
    for cut in cut_points:
        if (cut - last_cut_point) >= min_segment_length:
            adjusted_cut_points.append(cut)
            last_cut_point = cut

    return adjusted_cut_points

# Fonction pour couper la vidéo
def cut_video(video_path, cut_points, output_dir):
    video = mp.VideoFileClip(video_path)
    duration = video.duration

    segment_start = 0
    for idx, segment_end in enumerate(cut_points + [duration]):
        if segment_end - segment_start >= 60:
            segment_path = os.path.join(output_dir, f"segment_{idx + 1}.mp4")
            ffmpeg_extract_subclip(video_path, segment_start, segment_end, targetname=segment_path)
            segment_start = segment_end

# Fonction principale
def main():
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

if __name__ == '__main__':
    main()
