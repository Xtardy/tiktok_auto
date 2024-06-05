from pytube import YouTube
import os

def download_video(url, output_path='.', proxy=None):
    try:
        yt = YouTube(url, proxies={"http": proxy, "https": proxy})
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        stream.download(output_path=output_path)
        print(f'Successfully downloaded: {yt.title}')
    except Exception as e:
        print(f'Error downloading {url}: {e}')

def main():
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

if __name__ == '__main__':
    main()
