from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv
import streamlit as st
from transformers import pipeline

load_dotenv()

def get_youtube_transcript(video_url: str):
    # extract video ID from URL
    if "v=" in video_url:
        video_id = video_url.split("v=")[1]
        # Handle additional parameters
        if "&" in video_id:
            video_id = video_id.split("&")[0]
    else:
        st.error("Invalid YouTube URL format")
        return None

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        # combine all text entries into a single string
        full_transcript = " ".join([entry['text'] for entry in transcript])
        return full_transcript
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
        return None

@st.cache_resource
def load_summarizer():
    # Load the BART model for summarization
    return pipeline("summarization", model="facebook/bart-large-cnn")
    
def summarize_transcript():
    st.title("YouTube Transcript Summarizer")
    
    # Load the summarizer model
    summarizer = load_summarizer()
    
    video_url = st.text_input("Input YouTube URL")

    # Add sliders for parameters
    col1, col2 = st.columns(2)
    with col1:
        max_length = st.slider("Summary Length (tokens)", 100, 500, 250, 10)
    with col2:
        min_length = st.slider("Minimum Length (tokens)", 30, 200, 100, 10)

    # Create a button to trigger the start of the summarization
    if st.button("Summarize"):
        if not video_url:
            st.warning("Please enter a YouTube URL")
            return
        
        transcript = get_youtube_transcript(video_url)

        if transcript:
            with st.spinner("Generating summary..."):
                try:
                    # Generate summary using BART model
                    summary_output = summarizer(transcript, max_length=max_length, min_length=min_length, do_sample=False)
                    summary = summary_output[0]['summary_text']
                    
                    st.subheader("Summary")
                    st.markdown(summary)

                    # File name input for download
                    file_name = st.text_input("Enter file name for download (without extension):", "youtube_summary")
                    
                    # Add download button for summary
                    st.download_button(
                        label="Download summary as markdown",
                        data=summary,
                        file_name=f"{file_name}.md",
                        mime="text/markdown"
                    )
                except Exception as e:
                    st.error(f"Error generating summary: {e}")
        else:
            st.warning("Could not retrieve transcript. Please check the URL and try again.")

if __name__ == "__main__":
    summarize_transcript()
