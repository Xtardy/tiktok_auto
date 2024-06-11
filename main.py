import moviepy.editor as mp
import os
from pydub import AudioSegment, silence
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from pytube import YouTube
import numpy as np
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, ColorClip, AudioFileClip, CompositeAudioClip
from PIL import Image, ImageDraw, ImageFont
import srt
from datetime import timedelta
from youtube_transcript_api import YouTubeTranscriptApi
import requests
import random
import re
# Fonction pour enlever le son d'un clip
def remove_audio(clip):
    return clip.without_audio()

# Fonction pour recadrer un clip
def crop_clip(clip, crop_percentage):
    width, height = clip.size
    x_crop = int(width * crop_percentage)
    return clip.crop(x1=x_crop, x2=width - x_crop)

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
    img = Image.new('RGBA', video_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_path = "AvenirNext-Regular.ttf"
    font = ImageFont.truetype(font_path, 58)
    
    # Split the text into lines that fit within the video width
    max_width = video_size[0] - 40  # Padding of 20 pixels on each side
    lines = []
    words = text.split(' ')
    current_line = words[0]
    
    for word in words[1:]:
        test_line = f"{current_line} {word}"
        test_width = draw.textbbox((0, 0), test_line, font=font)[2] - draw.textbbox((0, 0), test_line, font=font)[0]
        if test_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    
    # Calculate the position for each line
    line_height = draw.textbbox((0, 0), lines[0], font=font)[3] - draw.textbbox((0, 0), lines[0], font=font)[1]
    y_offset = video_size[1] - len(lines) * line_height - 600  # Adjust the vertical position
    outline_range = 4
    
    for line in lines:
        text_bbox = draw.textbbox((0, 0), line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (video_size[0] - text_width) // 2
        text_y = y_offset

        # Draw outline
        for adj in range(-outline_range, outline_range + 1):
            draw.text((text_x + adj, text_y), line, font=font, fill="black")
            draw.text((text_x, text_y + adj), line, font=font, fill="black")

        for adj in [(i, j) for i in range(-outline_range, outline_range + 1) for j in range(-outline_range, outline_range + 1)]:
            draw.text((text_x + adj[0], text_y + adj[1]), line, font=font, fill="black")
        
        # Draw text
        draw.text((text_x, text_y), line, font=font, fill="yellow")
        y_offset += line_height
    
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
            
            subtitle_img = generate_subtitle_image(text, video_clip.size)
            subtitle_clip = ImageClip(subtitle_img).set_start(start_time).set_duration(end_time - start_time).set_position(('center', 'bottom'))
            subtitles.append(subtitle_clip)
    return subtitles

def add_subtitles_to_video(video_path, srt_path, output_path):
    video_clip = VideoFileClip(video_path)
    subtitles = generate_subtitles_from_srt(video_clip, srt_path)
    final_clip = CompositeVideoClip([video_clip] + subtitles)
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

def process_video_subtitles(video_path, transcript_path, output_dir):
    try:
        transcript = read_transcript(transcript_path)
        segments = parse_transcript(transcript)
        
        # Generate SRT file path
        output_srt_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}.srt")
        generate_srt_from_segments(segments, output_srt_path)
        
        # Generate output video path
        output_video_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}_with_subtitles.mp4")
        add_subtitles_to_video(video_path, output_srt_path, output_video_path)
        
        print(f"Processed video saved to {output_video_path}")
    except ValueError as e:
        print(f"Error: {e}")

def download_video(url, output_path='.', proxy=None):
    try:
        yt = YouTube(url, proxies={"http": proxy, "https": proxy})
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        video_path = stream.download(output_path=output_path)
        transcript = get_transcript(yt.video_id)
        if transcript:
            transcript_file_path = video_path.replace('.mp4', '.srt')
            save_transcript_to_file(transcript, transcript_file_path)
            print(f'Successfully downloaded: {yt.title} with transcript')
        else:
            print(f'Successfully downloaded: {yt.title} without transcript')
    except Exception as e:
        print(f'Error downloading {url}: {e}')

def extract_audio_from_video(video_path, output_audio_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(output_audio_path)
    audio_clip.close()
    video_clip.close()

def find_cut_points(audio_path, min_silence_len=1000, silence_thresh=-40):
    audio = AudioSegment.from_file(audio_path)
    silences = silence.detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    cut_points = [(start + (stop - start) // 2) / 1000 for start, stop in silences]
    return cut_points

def adjust_cut_points(cut_points, min_segment_length=60):
    adjusted_cut_points = []
    last_cut_point = 0
    for cut in cut_points:
        if (cut - last_cut_point) >= min_segment_length:
            adjusted_cut_points.append(cut)
            last_cut_point = cut
    return adjusted_cut_points

def cut_video(video_path, cut_points, output_dir):
    video = mp.VideoFileClip(video_path)
    duration = video.duration
    segment_start = 0
    for idx, segment_end in enumerate(cut_points + [duration]):
        if segment_end - segment_start >= 60:
            segment_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}_segment_{idx + 1}.mp4")
            ffmpeg_extract_subclip(video_path, segment_start, segment_end, targetname=segment_path)
            segment_start = segment_end


def convert_time_to_seconds(time_str):
    return float(time_str.replace(',', '.'))

def convert_seconds_to_time(seconds):
    seconds = float(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{seconds:.2f}"

def adjust_block_timing(block, segment_start):
    lines = block.split('\n')
    time_range = lines[0]
    start_time_str, end_time_str = time_range.split('-->')
    start_time = convert_time_to_seconds(start_time_str)
    end_time = convert_time_to_seconds(end_time_str)
    adjusted_start = start_time - segment_start
    adjusted_end = end_time - segment_start
    adjusted_time_range = f"{convert_seconds_to_time(adjusted_start)} --> {convert_seconds_to_time(adjusted_end)}"
    return block.replace(time_range, adjusted_time_range)

def cut_transcript(transcript_path, cut_points, output_dir):
    with open(transcript_path, 'r', encoding='utf-8') as file:
        transcript_content = file.read()
    
    # Split the transcript into blocks
    blocks = transcript_content.strip().split('\n\n')
    segments = []
    
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 2 and '-->' in lines[0]:
            time_range = lines[0]
            start_time_str, end_time_str = time_range.split('-->')
            start_time = convert_time_to_seconds(start_time_str)
            end_time = convert_time_to_seconds(end_time_str)
            segments.append((start_time, end_time, block))

    for idx, segment_end in enumerate(cut_points + [segments[-1][1]]):
        segment_transcript_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(transcript_path))[0]}_segment_{idx + 1}.srt")
        segment_start = cut_points[idx - 1] if idx > 0 else 0
        segment_blocks = []

        for start, end, block in segments:
            if start >= segment_start and end <= segment_end:
                adjusted_block = adjust_block_timing(block, segment_start)
                segment_blocks.append(adjusted_block)
        
        with open(segment_transcript_path, 'w', encoding='utf-8') as segment_file:
            segment_file.write('\n\n'.join(segment_blocks))


def save_transcript_to_file(transcript, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for entry in transcript:
            start = entry['start']
            duration = entry['duration']
            text = entry['text']
            file.write(f"{start:.2f} --> {start + duration:.2f}\n{text}\n\n")

def setup_proxy(proxy):
    session = requests.Session()
    session.proxies.update(proxy)
    return session

def get_transcript(video_id, languages=['en']):
    try:
        proxy = 'http://cache.univ-st-etienne.fr:3128'
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages, proxies=proxy)
        filtered_transcript = filter_transcript(transcript)
        return filtered_transcript
    except Exception as e:
        print(f"Error: {e}")
        return None

def filter_transcript(transcript):
    filtered_transcript = []
    for entry in transcript:
        text = entry['text']
        # Use regex to remove all occurrences of names in uppercase followed by a colon
        text = re.sub(r'\b[A-Z ]+:\s*', '', text)
        filtered_transcript.append({
            'start': entry['start'],
            'duration': entry['duration'],
            'text': text
        })
    return filtered_transcript

def main():
    gameplay_path = 'gameplay_videos'
    background_music_path = 'background_music'
    links_file = 'links/links.txt'
    output_dir = 'downloaded_videos'
    proxy = 'http://cache.univ-st-etienne.fr:3128'

    segments_path = "videos_cut"
    gameplay_output_path = 'output_with_gameplay'
    music_output_path = 'output_with_music'
    final_output_path = 'final_output'
    audio_temp_path = 'audio_temp.mp3'
    
    crop_percentage = 0.15
    final_width = 720
    final_height = 1280
    padding = 0
    background_music_volume = 0.2

    
    print("Téléchargement des vidéos...")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(links_file, 'r') as file:
        links = file.readlines()

    for link in links:
        url = link.strip()
        if url:
            download_video(url, output_dir, proxy)
    
    print("Couper les vidéos...")

    if not os.path.exists(audio_temp_path):
        first_video = next((f for f in os.listdir(output_dir) if f.endswith(('.mp4', '.avi', '.mov'))), None)
        if first_video:
            video_path = os.path.join(output_dir, first_video)
            extract_audio_from_video(video_path, audio_temp_path)
        else:
            print("Erreur: Aucune vidéo disponible pour extraire l'audio.")
            return
    
    cut_points = find_cut_points(audio_temp_path, min_silence_len=1000, silence_thresh=-40)
    cut_points = adjust_cut_points(cut_points, min_segment_length=60)

    if not os.path.exists(segments_path):
        os.makedirs(segments_path)

    for video_file in os.listdir(output_dir):
        if video_file.endswith(('.mp4', '.avi', '.mov')):
            video_path = os.path.join(output_dir, video_file)
            cut_video(video_path, cut_points, segments_path)
            
            transcript_file = video_path.replace('.mp4', '.srt')
            if os.path.exists(transcript_file):
                cut_transcript(transcript_file, cut_points, segments_path)

    print("Ajout du gameplay aux vidéos...")
    if not os.path.exists(gameplay_output_path):
        os.makedirs(gameplay_output_path)

    segment_videos = [os.path.join(segments_path, f) for f in os.listdir(segments_path) if f.endswith(('.mp4', '.avi', '.mov'))]
    gameplay_videos = [os.path.join(gameplay_path, f) for f in os.listdir(gameplay_path) if f.endswith(('.mp4', '.avi', '.mov'))]


    for segment_video in segment_videos:
        segment_clip = VideoFileClip(segment_video)
        gameplay_video = random.choice(gameplay_videos)
        gameplay_clip = VideoFileClip(gameplay_video)
        gameplay_clip = remove_audio(gameplay_clip)

        if gameplay_clip.duration > segment_clip.duration:
            gameplay_clip = gameplay_clip.subclip(0, segment_clip.duration)

        segment_clip = crop_clip(segment_clip, crop_percentage)
        gameplay_clip = crop_clip(gameplay_clip, crop_percentage)
        segment_clip = segment_clip.resize(width=final_width)
        gameplay_clip = gameplay_clip.resize(width=final_width)
        total_height = segment_clip.h + gameplay_clip.h + padding
        segment_clip = segment_clip.set_position(("center", "top"))
        gameplay_clip = gameplay_clip.set_position(("center", segment_clip.h + padding))
        black_bar = ColorClip(size=(final_width, padding), color=(0, 0, 0)).set_duration(segment_clip.duration)

        final_clip = CompositeVideoClip([segment_clip, black_bar.set_position(("center", segment_clip.h)), gameplay_clip], size=(final_width, total_height))

        if total_height < final_height:
            top_black = ColorClip(size=(final_width, (final_height - total_height) // 2), color=(0, 0, 0)).set_duration(segment_clip.duration)
            bottom_black = ColorClip(size=(final_width, (final_height - total_height + 1) // 2), color=(0, 0, 0)).set_duration(segment_clip.duration)
            final_clip = CompositeVideoClip([top_black.set_position(("center", "top")), final_clip.set_position(("center", top_black.h)), bottom_black.set_position(("center", top_black.h + total_height))], size=(final_width, final_height))

        output_filename = os.path.join(gameplay_output_path, f"combined_{os.path.basename(segment_video)}")
        final_clip.write_videofile(output_filename, codec='hevc_nvenc', audio_codec='aac')

    print("Traitement terminé!")

    print("Ajout des sons aux vidéos...")
    if not os.path.exists(music_output_path):
        os.makedirs(music_output_path)

    
    background_music_files = [os.path.join(background_music_path, f) for f in os.listdir(background_music_path) if f.endswith(('.mp3', '.wav', '.ogg'))]

    for video_file in os.listdir(gameplay_output_path):
        if video_file.endswith(('.mp4', '.avi', '.mov')):
            video_path = os.path.join(gameplay_output_path, video_file)
            video_clip = VideoFileClip(video_path)
            background_music_file = random.choice(background_music_files)
            background_music = AudioFileClip(background_music_file).volumex(background_music_volume)

            if background_music.duration > video_clip.duration:
                background_music = background_music.subclip(0, video_clip.duration)

            background_music = background_music.set_duration(video_clip.duration)
            final_audio = CompositeAudioClip([video_clip.audio, background_music])
            final_clip = video_clip.set_audio(final_audio)
            output_filename = os.path.join(music_output_path, os.path.basename(video_file))
            final_clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')

    print("Ajout de la musique de fond terminé!")

    print("Ajout des sous-titres aux vidéos...")
    if not os.path.exists(final_output_path):
        os.makedirs(final_output_path)

    for video_file in os.listdir(music_output_path):
        if video_file.endswith(('.mp4', '.avi', '.mov')):
            video_path = os.path.join(music_output_path, video_file)
            
            # Remove 'combined_' prefix to find the matching transcript
            transcript_basename = video_file.replace('combined_', '').replace('.mp4', '.srt').replace('.avi', '.srt').replace('.mov', '.srt')
            transcript_file = os.path.join(segments_path, transcript_basename)
            
            if os.path.exists(transcript_file):
                output_srt_path = os.path.join(final_output_path, os.path.basename(transcript_file))
                process_video_subtitles(video_path, transcript_file, final_output_path)
            else:
                print(f"Transcript file not found for {video_file}")


    print("Toutes les étapes sont complétées!")

if __name__ == "__main__":
    main()
