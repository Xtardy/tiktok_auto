from datetime import timedelta
import re

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def read_srt(file_path):
    """Read SRT file and convert to list of dicts with start, end, and word"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)\n', re.DOTALL)
    matches = pattern.findall(content)

    transcript = []
    for match in matches:
        start_time = srt_timestamp_to_seconds(match[1])
        end_time = srt_timestamp_to_seconds(match[2])
        words = match[3].replace('\n', ' ').split()
        for word in words:
            transcript.append({"start": start_time, "end": end_time, "word": word})
    
    return transcript

def srt_timestamp_to_seconds(timestamp):
    """Convert SRT timestamp to seconds"""
    hours, minutes, seconds = timestamp.split(':')
    seconds, milliseconds = seconds.split(',')
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
    return total_seconds

def segment_transcript(transcript, min_duration=1.0, max_duration=1000.0, max_words=10):
    subtitles = []
    current_subtitle = {"start": None, "end": None, "text": ""}
    for entry in transcript:
        if current_subtitle["start"] is None:
            current_subtitle["start"] = entry["start"]
        
        current_text = current_subtitle["text"] + (" " if current_subtitle["text"] else "") + entry["word"]
        current_end = entry["end"]
        
        duration = current_end - current_subtitle["start"]
        word_count = len(current_text.split())

        if (duration > max_duration) or (word_count > max_words) or (duration >= min_duration and word_count >= max_words // 2):
            current_subtitle["end"] = current_end
            subtitles.append(current_subtitle)
            current_subtitle = {"start": entry["start"], "end": None, "text": entry["word"]}
        else:
            current_subtitle["text"] = current_text
            current_subtitle["end"] = current_end

    if current_subtitle["text"]:
        current_subtitle["end"] = current_end
        subtitles.append(current_subtitle)

    return subtitles

def format_subtitles_srt(subtitles):
    srt_content = ""
    for index, subtitle in enumerate(subtitles):
        start_time = format_timestamp(subtitle["start"])
        end_time = format_timestamp(subtitle["end"])
        srt_content += f"{index + 1}\n{start_time} --> {end_time}\n{subtitle['text']}\n\n"
    return srt_content


