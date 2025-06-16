import os 
import re
import requests 
import pandas as pd
import json
from bs4 import BeautifulSoup as bs
from youtube_transcript_api import YouTubeTranscriptApi

def get_video_details(soup):
    title = channel = description = video_id = external_links = None
    data = re.search(r'var ytInitialPlayerResponse = (\{.*?\});', soup.prettify())
    if data:
        data = json.loads(data.group(1))
        video_details = data.get('videoDetails', {})
        title = video_details.get("title")
        channel = video_details.get("author")
        description = video_details.get("shortDescription")
        video_id = video_details.get("videoId")
        external_links = re.findall(r'(https?://\S+)', description)
    return title, channel, description, video_id, external_links

def get_single_utube_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list:
            transcript_en = transcript.translate("en").fetch()
            transcript_en_text = " ".join([segment["text"] for segment in transcript_en])
            return transcript_en_text
    except Exception as e:
        print(f"Transcript fetch failed for video: {video_id}: {e}")
    
    return None

def get_bulk_utube_trancript(video_ids):
    try:
        transcript_dict = {}
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_ids)

        for idx, transcript in enumerate(transcript_list):
            transcript_en = transcript.translate("en").fetch()
            transcript_en_text = " ".join([segment["text"] for segment in transcript_en])
            transcript_dict[video_ids[idx]] = transcript_en_text
        return transcript_dict
    
    except Exception as e:
        print(f"Transcript fetching failed for videos: {e}")

    return None

def get_data_path():
    folder_name = "data"
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(curr_dir, folder_name)
    return data_path

def save_channel_data_df(df, channel_name):
    channel_path = os.path.join(get_data_path(), channel_name)
    file_path = os.path.join(get_data_path(), channel_name, channel_name+".csv")
    os.makedirs(channel_path, exists_ok = True)
    df.to_csv(file_path, index = False)

def scrape_youtube(video_ids):
    infos = {
        "title": [],
        "channel": [],
        "description": [],
        "video_id": [],
        "external_link": [],
        "transcript": [],
    }

    for video_id in video_ids:
        transcript = get_single_utube_transcript(video_id)
        url = f"https://www.youtube.com/watch?v={video_id}"

        response = requests.get(url)
        soup = bs(response.text, 'html.parser')
        video_details = get_video_details(soup)
        infos["title"].append(video_details[0] if video_details[0] is not None else '')
        infos["channel"].append(video_details[1] if video_details[1] is not None else '')
        infos["description"].append(video_details[2] if video_details[2] is not None else '')
        infos["video_id"].append(video_details[3] if video_details[3] is not None else '')
        infos["external_link"].append(video_details[4] if video_details[4] is not None else [])
        infos["transcript"].append(transcript if transcript is not None else '')

    df = pd.DataFrame(infos)
    save_channel_data_df(df, infos["channel"][0])
    return df

def get_channel_data_df(channel_name):
    file_path = os.path.join(get_data_path(), channel_name, channel_name + ".csv")
    df = pd.read_csv(file_path)
    return df

def get_channel_list():
    data_path = get_data_path()
    return os.listdir(data_path)

def fetch_videoid(path, channel_name):
    channel_dir = os.path.join(get_data_path(), channel_name)
    video_id = path.replace(channel_dir, "").split(".")[0][1:]
    return video_id
    
def scrape_channel_id_and_icon(url):
    icon_link = channel_id = None
    response = requests.get(url)
    soup = bs(response.text, 'html.parser')

    for link in soup.find_all("link", href=True):
        href = link["href"]
        if href.startswith('https://yt3.googleusercontent.com'):
            icon_link = href
        elif href.startswith('https://www.youtube.com/channel'):
            channel_id = href.replace("https://www.youtube.com/channel/","")

    return icon_link, channel_id