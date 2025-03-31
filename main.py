import streamlit as st
from streamlit_cookies_controller import CookieController
from youtube_transcript_api import YouTubeTranscriptApi
import os
import requests
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta

load_dotenv()

# Initialize the cookie controller
cookie_controller = CookieController()

# Initialize session state for rate limiting
if 'api_calls' not in st.session_state:
    # Try to get the API calls from cookies
    api_calls = cookie_controller.get('api_calls')
    st.session_state.api_calls = int(api_calls) if api_calls else 0

if 'last_reset_time' not in st.session_state:
    # Try to get the last reset time from cookies
    last_reset = cookie_controller.get('last_reset_time')
    st.session_state.last_reset_time = float(last_reset) if last_reset else time.time()

# Rate limit configuration
MAX_CALLS_PER_DAY = 5
RESET_PERIOD = 86400  # 24 hours in seconds (daily reset)

def check_rate_limit():
    current_time = time.time()
    if current_time - st.session_state.last_reset_time > RESET_PERIOD:
        st.session_state.api_calls = 0
        st.session_state.last_reset_time = current_time
        # Update cookies
        cookie_controller.set('api_calls', '0')
        cookie_controller.set('last_reset_time', str(current_time))
    
    if st.session_state.api_calls >= MAX_CALLS_PER_DAY:
        time_until_reset = RESET_PERIOD - (current_time - st.session_state.last_reset_time)
        hours, remainder = divmod(int(time_until_reset), 3600)
        minutes, seconds = divmod(remainder, 60)
        return False, f"Daily limit reached. Resets in {hours}h {minutes}m {seconds}s."
    
    return True, ""

def get_youtube_transcript(video_url: str):
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
        full_transcript = " ".join([entry['text'] for entry in transcript])
        return full_transcript
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
        return None

def summarize_transcript():
    st.title("YouTube Transcript Summarizer")
    
    remaining_calls = MAX_CALLS_PER_DAY - st.session_state.api_calls
    st.sidebar.info(f"API Calls Remaining Today: {remaining_calls}/{MAX_CALLS_PER_DAY}")
    
    if st.session_state.api_calls > 0:
        current_time = time.time()
        time_until_reset = RESET_PERIOD - (current_time - st.session_state.last_reset_time)
        reset_time = datetime.now() + timedelta(seconds=time_until_reset)
        st.sidebar.text(f"Resets at: {reset_time.strftime('%H:%M:%S, %b %d')}")

    video_url = st.text_input("Input YouTube URL")

    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider("Temperature (Randomness)", 0.0, 1.0, 0.5, 0.01)
    with col2:
        presence_penalty = st.slider("Presence Penalty (Likelihood of discussing new topics)", 0.0, 1.0, 0.05, 0.01)

    if st.button("Summarize"):
        if not video_url:
            st.warning("Please enter a YouTube URL")
            return
        
        can_proceed, message = check_rate_limit()
        if not can_proceed:
            st.warning(message)
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
                "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
                "Content-Type": "application/json"
            }

            try:
                response = requests.post(url, json=payload, headers=headers)
                response_json = response.json()

                if "choices" in response_json and len(response_json['choices']) > 0:
                    # Increment the API call counter
                    st.session_state.api_calls += 1
                    # Update cookie
                    cookie_controller.set('api_calls', str(st.session_state.api_calls))
                    
                    summary = response_json["choices"][0]["message"]["content"]
                    st.markdown(summary)

                    # User input for file name
                    file_name = st.text_input("Enter file name for download (without extension):", "youtube_summary")
                    
                    st.download_button(
                        label="Download summary as markdown",
                        data=summary,
                        file_name=f"{file_name}.md",
                        mime="text/markdown"
                    )
                else:
                    st.error(f"Error in API response: {response_json}")
            except Exception as e:
                st.error(f"Error calling Perplexity API: {e}")


if __name__ == "__main__":
    summarize_transcript()
