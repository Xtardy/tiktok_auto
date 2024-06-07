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
  
        
  

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        