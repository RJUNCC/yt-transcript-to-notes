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

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab')

load_dotenv()

def get_youtube_transcript(video_url: str):
    if "v=" in video_url:
        video_id = video_url.split("v=")[1].split("&")[0]
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

    col1, col2 = st.columns(2)
    with col1:
        summarizer_type = st.selectbox("Summarization Algorithm", ["LexRank", "LSA", "Luhn"])
    with col2:
        sentences_count = st.slider("Number of Sentences", 5, 30, 10)

    if st.button("Summarize"):
        if not video_url:
            st.warning("Please enter a YouTube URL")
            return
        
        transcript = get_youtube_transcript(video_url)

        if transcript:
            st.info("Generating summary...")
            
            try:
                summary = summarize_text(transcript, summarizer_type, sentences_count)
                
                st.subheader("Summary")
                st.markdown(summary)

                st.subheader("Structured Notes")
                sentences = summary.split(". ")
                for i, sentence in enumerate(sentences):
                    if sentence:
                        st.markdown(f"**Point {i+1}:** {sentence}")
                
                file_name = st.text_input("Enter file name for download (without extension):", "youtube_summary")
                
                markdown_content = f"# YouTube Video Summary\n\n## Summary\n\n{summary}\n\n## Structured Notes\n\n"
                for i, sentence in enumerate(sentences):
                    if sentence:
                        markdown_content += f"**Point {i+1}:** {sentence}\n\n"
                
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
