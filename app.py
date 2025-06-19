import os
import requests
import scrapetube
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup as bs

import llm_service
import youtube_service
import constants as const

def scrape_youtube(video_ids):
    infos = {
        "title": [],
        "channel": [],
        "description": [],
        "video_id": [],
        "external_link": []
    }

    progress_bar = st.progress(0)
    for index, video_id in enumerate(video_ids):
        progress_bar.progress((index+1)/len(video_ids))
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url)
        soup = bs(response.text, 'html.parser')
        video_details = youtube_service.get_video_details(soup)

        title_str = video_details[0] if video_details[0] is not None else ''
        channel_str = video_details[1] if video_details[1] is not None else ''
        description_str = video_details[2] if video_details[2] is not None else ''
        video_id_str = video_details[3] if video_details[3] is not None else ''
        external_link_str = video_details[4] if video_details[4] is not None else []

        infos["title"].append(title_str)
        infos["channel"].append(channel_str)
        infos["description"].append(description_str)
        infos["video_id"].append(video_id_str)
        infos["external_link"].append(external_link_str)
    
    progress_bar.empty()
    df = pd.DataFrame(infos)
    df["is_trans_fetched"] = False
    channel_name = create_channel_name(infos["channel"][0])
    youtube_service.save_channel_data_df(df, channel_name)

    return df, channel_name

def create_channel_name(channel_name_input):
    channel_name = channel_name_input.replace(" ", "_").lower()
    return channel_name

def create_trans_txt_file(title_str, channel_str, description_str, video_id_str, transcript_str):
    text = (
        str(title_str) + "\n" +
        str(channel_str) + "\n" +
        str(description_str) + "\n" +
        str(video_id_str) + "\n" +
        str(transcript_str)
    )

    channel_str = create_channel_name(channel_str)
    data_path = youtube_service.get_data_path()
    channel_path = os.path.join(data_path, channel_str)
    encoded = channel_path.encode("utf-8")
    os.makedirs(encoded, exist_ok = True)
    file_path = video_id_str + ".txt"
    file_path = os.path.join(channel_path, file_path)
    with open(file_path, 'w', encoding = "utf-8") as file:
        file.write(text)

def fetch_transcript(df):
    title_list = df["title"].tolist()
    description_list = df["description"].tolist()
    channel_list = df["channel"].tolist()
    video_id_list = df["video_id"].tolist()
    is_trans_fetched = df["is_trans_fetched"].tolist()

    if "transcript" not in df.columns:
        df["transcript"] = ""
    
    channel_name = create_channel_name(channel_list[0])
    progress_bar = st.progress(0)
    for index, video_id in enumerate(video_id_list):
        progress_bar.progress((index+1)/len(video_id_list))
        if is_trans_fetched[index] == False:
            transcript = youtube_service.get_single_utube_transcript(video_id)
            create_trans_txt_file(title_list[index], description_list[index], channel_name, video_id, transcript)
            llm_service.create_kb(channel_name, video_id)
            df.loc[index, "transcript"] = transcript
            df.loc[index, "is_trans_fetched"] = True
            youtube_service.save_channel_data_df(df, channel_name)
    st.write("Vector DB updated")
    progress_bar.empty()

#Streamlit page
st.set_page_config(layout = "wide")
page = st.sidebar.radio(
    "Page Navigator",
    [
        const.YT_EXTRACT_PAGE,
        const.YT_RAG_PAGE
    ],
)
st.header("Youtube RAG QA Application")

if page == const.YT_EXTRACT_PAGE:

    channel_link = st.text_input("Enter Channel Link", "")
    fetch_button = st.button("Create KB")

    if fetch_button and len(channel_link) > 5:
        icon, channel_id = youtube_service.scrape_channel_id_and_icon(channel_link)
        video_ids = scrapetube.get_channel(channel_id)
        video_id_list = []
        
        for id in video_ids:
            video_id_list.append(id["videoId"])

        num_videos = len(video_id_list)
        df, channel_name = scrape_youtube(video_id_list)
        st.write(f"Found {num_videos} videos")
        fetch_transcript(df)

if page == const.YT_RAG_PAGE:

    channel_list = youtube_service.get_channel_list()
    channel_list.insert(0, const.SEL_CHANL)
    selected = st.sidebar.selectbox(const.SEL_CHANL, channel_list)
    query = st.text_input("User Query", "")

    if selected and selected != const.SEL_CHANL:
        channel_df = youtube_service.get_channel_data_df(selected)
        if not channel_df.empty:
            with st.expander("Show Video Metadata"):
                st.dataframe(channel_df)

    if len(query) > 10 and selected != const.SEL_CHANL:
        answer, source_documents, video_ids = llm_service.get_response(query, selected)
        st.write(answer)

        if (len(source_documents) > 0):
            with st.expander("View Source Chunks and Video Id's"):
                ctr = 1
                for index, source_doc in enumerate(source_documents):
                    st.write(f"Chunk: {ctr}")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(source_doc)
                    with col2:
                        url = f"https://www.youtube.com/watch?v={video_ids[index]}"
                        st.video(url)
                    ctr += 1 