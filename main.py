from youtube_transcript_api import YouTubeTranscriptApi
import os
import requests
from dotenv import load_dotenv
import streamlit as st
from transformers import pipeline

load_dotenv()

# Load the summarization model
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

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
    
def chunk_text(text, max_chunk_size=1000):
    """Split text into chunks of approximately max_chunk_size characters."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        if current_size + len(word) + 1 > max_chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_size = len(word)
        else:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for the space
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

def summarize_transcript():
    st.title("YouTube Transcript Summarizer")
    
    # Load the summarizer model
    with st.spinner("Loading summarization model..."):
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
                    # Split transcript into chunks if it's too long
                    chunks = chunk_text(transcript)
                    chunk_summaries = []
                    
                    # Process each chunk
                    for i, chunk in enumerate(chunks):
                        st.text(f"Processing chunk {i+1}/{len(chunks)}...")
                        chunk_summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
                        chunk_summaries.append(chunk_summary[0]['summary_text'])
                    
                    # Combine chunk summaries
                    if len(chunk_summaries) > 1:
                        combined_summary = " ".join(chunk_summaries)
                        # Summarize the combined summaries for a more coherent final summary
                        final_summary = summarizer(combined_summary, max_length=max_length, min_length=min_length, do_sample=False)
                        summary = final_summary[0]['summary_text']
                    else:
                        summary = chunk_summaries[0]
                    
                    st.subheader("Summary")
                    st.markdown(summary)
                    
                    # Structure the summary into bullet points
                    st.subheader("Key Points")
                    sentences = summary.split(". ")
                    for i, sentence in enumerate(sentences):
                        if sentence.strip():
                            st.markdown(f"- {sentence.strip()}")
                    
                    # File name input for download
                    file_name = st.text_input("Enter file name for download (without extension):", "youtube_summary")
                    
                    # Format markdown for download
                    markdown_content = f"# YouTube Video Summary\n\n## Summary\n\n{summary}\n\n## Key Points\n\n"
                    for sentence in sentences:
                        if sentence.strip():
                            markdown_content += f"- {sentence.strip()}\n"
                    
                    # Add download button for summary
                    st.download_button(
                        label="Download summary as markdown",
                        data=markdown_content,
                        file_name=f"{file_name}.md",
                        mime="text/markdown"
                    )
                except Exception as e:
                    st.error(f"Error generating summary: {e}")
                    st.error("If you're seeing an error related to the model, make sure you have the transformers library installed with 'pip install transformers torch'")
        else:
            st.warning("Could not retrieve transcript. Please check the URL and try again.")

if __name__ == "__main__":
    summarize_transcript()
