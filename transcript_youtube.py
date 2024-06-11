from youtube_transcript_api import YouTubeTranscriptApi
import requests

# Define your proxy settings
proxy = {
    'http': 'http://cache.univ-st-etienne.fr:3128',
    'https': 'https://cache.univ-st-etienne.fr:3128',
}

# Function to set up requests to use the proxy
def setup_proxy(proxy):
    session = requests.Session()
    session.proxies.update(proxy)
    return session

# Set up the proxy for requests
session = setup_proxy(proxy)

# Use YouTubeTranscriptApi with the session that uses the proxy
def get_transcript(video_id, languages=['en']):
    """
    Download transcript for a given YouTube video ID.

    :param video_id: str, YouTube video ID
    :param languages: list of str, languages to look for the transcript
    :return: list of dict, each containing 'text', 'start', and 'duration'
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages, proxies=proxy)
        return transcript
    except Exception as e:
        print(f"Error: {e}")
        return None

def save_transcript_to_file(transcript, file_path):
    """
    Save transcript to a file.

    :param transcript: list of dict, transcript data
    :param file_path: str, file path to save the transcript
    """
    with open(file_path, 'w', encoding='utf-8') as file:
        for entry in transcript:
            start = entry['start']
            duration = entry['duration']
            text = entry['text']
            file.write(f"{start:.2f} --> {start + duration:.2f}\n{text}\n\n")

# Example usage
video_id = 'MS5UjNKw_1M'
transcript = get_transcript(video_id)
if transcript:
    save_transcript_to_file(transcript, 'transcript.txt')
