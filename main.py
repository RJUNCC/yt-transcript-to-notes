from youtube_transcript_api import YouTubeTranscriptApi
import os
from openai import OpenAI
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

def get_youtube_transcript(video_url: str):
    # extract video ID from URL
    video_id = video_url.split("v=")[1]

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        # combine all text entries into a single string
        full_transcript = " ".join([entry['text'] for entry in transcript])



        return full_transcript
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None
    
def summarize_transcript():
    st.title("YouTube Transcript Summarizer")

    video_url = st.text_input("Input YouTube URL")

    # Add sliders for paramaters
    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider("Temperature (Randomness)", 0.0, 1.0, 0.5, 0.01)
    with col2:
        presence_penalty = st.slider("Presence Penalty (Likelihood of discussing new topics)", 0.0, 1.0, 0.05, 0.01)

    # Create a button to trigger the start of the summarization
    if st.button("Summarize"):
        if not video_url:
            st.warning("Please enter a YouTube URL")
            return
        
        transcript = get_youtube_transcript(video_url)

        if transcript:
            st.info("Generating summary...")

            url = "https://api.perplexity.ai/chat/completions"

            payload = {
                "model": "sonar-pro",
                "messages": [
                    {"role": "user", "content": f"Define everything so it's clear, summarize this transcript into high quality and organized notes, and provide 3-5 examples, analogies, anything to help understand, then in the end provide additional resources:{transcript}"}
                ],
                "max_tokens": 1000,
                "temperature": temperature,
                "presence_penalty": presence_penalty

            }

            headers = {
                "Authorization": f"Bearer {os.getenv("PERPLEXITY_API_KEY")}",
                "Content-Type": "application/json"
            }

            try:
                response = requests.post(url, json=payload, headers=headers)
                response_json = response.json()

                if "choices" in response_json and len(response_json['choices']) > 0:
                    
                    summary = response.json().get("choices")[0].get("message").get("content")
                    st.markdown(summary)

                    # add download button for summary
                    st.download_button(
                        label="Download summary as markdown",
                        data=summary,
                        file_name="youtube_summary.md",
                        mime="text/markdown"
                    )
                else:
                    st.error(f"Error in API response: {response_json}")
            except Exception as e:
                st.error(f"Error calling Perplexity API: {e}")

if __name__ == "__main__":
    summarize_transcript()
