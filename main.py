from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv
import streamlit as st
import nltk
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
import time

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

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

def summarize_text(text, summarizer_type, sentences_count=10):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    
    if summarizer_type == "LexRank":
        summarizer = LexRankSummarizer()
    elif summarizer_type == "LSA":
        summarizer = LsaSummarizer()
    else:  # Luhn
        summarizer = LuhnSummarizer()
        
    summary = summarizer(parser.document, sentences_count)
    return " ".join([str(sentence) for sentence in summary])
    
def summarize_transcript():
    st.title("YouTube Transcript Summarizer")
    
    video_url = st.text_input("Input YouTube URL")

    # Add options for summarization
    col1, col2 = st.columns(2)
    with col1:
        summarizer_type = st.selectbox(
            "Summarization Algorithm",
            ["LexRank", "LSA", "Luhn"]
        )
    with col2:
        sentences_count = st.slider("Number of Sentences", 5, 30, 10)

    # Create a button to trigger the start of the summarization
    if st.button("Summarize"):
        if not video_url:
            st.warning("Please enter a YouTube URL")
            return
        
        transcript = get_youtube_transcript(video_url)

        if transcript:
            with st.spinner("Generating summary..."):
                start_time = time.time()
                
                try:
                    # Generate summary using selected algorithm
                    summary = summarize_text(transcript, summarizer_type, sentences_count)
                    
                    end_time = time.time()
                    st.success(f"Summary generated in {end_time - start_time:.2f} seconds")
                    
                    st.subheader("Summary")
                    st.markdown(summary)

                    # Add structured notes based on the summary
                    st.subheader("Structured Notes")
                    
                    # Split summary into sentences for structured notes
                    sentences = summary.split(". ")
                    for i, sentence in enumerate(sentences):
                        if sentence:  # Skip empty sentences
                            st.markdown(f"**Point {i+1}:** {sentence}")
                    
                    # File name input for download
                    file_name = st.text_input("Enter file name for download (without extension):", "youtube_summary")
                    
                    # Format markdown for download
                    markdown_content = f"# YouTube Video Summary\n\n## Summary\n\n{summary}\n\n## Structured Notes\n\n"
                    for i, sentence in enumerate(sentences):
                        if sentence:
                            markdown_content += f"**Point {i+1}:** {sentence}\n\n"
                    
                    # Add download button for summary
                    st.download_button(
                        label="Download summary as markdown",
                        data=markdown_content,
                        file_name=f"{file_name}.md",
                        mime="text/markdown"
                    )
                except Exception as e:
                    st.error(f"Error generating summary: {e}")
        else:
            st.warning("Could not retrieve transcript. Please check the URL and try again.")

if __name__ == "__main__":
    summarize_transcript()
