import datetime

transcript = [
    {"start": 0.0, "end": 1.0, "word": "Hello"},
    {"start": 1.0, "end": 2.0, "word": "world"},
    {"start": 2.0, "end": 3.5, "word": "this"},
    {"start": 3.5, "end": 4.0, "word": "is"},
    {"start": 4.0, "end": 5.0, "word": "a"},
    {"start": 5.0, "end": 6.0, "word": "test"},
    # Add more words with their start and end times
]

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def segment_transcript(transcript, min_duration=1.0, max_duration=4.0, max_words=10):
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
            subtitles.append(current_subtitle)
            current_subtitle = {"start": entry["start"], "end": None, "text": entry["word"]}
        else:
            current_subtitle["text"] = current_text
            current_subtitle["end"] = current_end

    if current_subtitle["text"]:
        subtitles.append(current_subtitle)

    return subtitles

def format_subtitles_srt(subtitles):
    srt_content = ""
    for index, subtitle in enumerate(subtitles):
        start_time = format_timestamp(subtitle["start"])
        end_time = format_timestamp(subtitle["end"])
        srt_content += f"{index + 1}\n{start_time} --> {end_time}\n{subtitle['text']}\n\n"
    return srt_content

subtitles = segment_transcript(transcript)
srt_content = format_subtitles_srt(subtitles)

with open("subtitles.srt", "w") as file:
    file.write(srt_content)
