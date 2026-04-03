"""Main Streamlit application for Voice Note Summarizer."""

import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.core.audio_recorder import AudioRecorder
from src.core.summarize import SummaryEngine
from src.core.transcribe import TranscriptionEngine
from src.core.tts_engine import TTSEngine

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


st.set_page_config(
    page_title="AI Voice Note Pro",
    page_icon="🎤",
    layout="wide",
)


if "transcription" not in st.session_state:
    st.session_state.transcription = ""
if "summary" not in st.session_state:
    st.session_state.summary = {}
if "action_items" not in st.session_state:
    st.session_state.action_items = []
if "transcriber" not in st.session_state:
    st.session_state.transcriber = None
if "summarizer" not in st.session_state:
    st.session_state.summarizer = SummaryEngine()
if "recording_complete" not in st.session_state:
    st.session_state.recording_complete = False
if "recorded_file" not in st.session_state:
    st.session_state.recorded_file = None


st.title("AI Voice Note Pro")
st.markdown("### Record • Upload • Transcribe • Summarize")


with st.sidebar:
    st.header("Settings")

    if st.session_state.summarizer.use_ai:
        st.success("AI Mode: OpenAI connected")
    else:
        st.warning("Local Mode: Add OPENAI_API_KEY to .env for AI summaries")

    model_size = st.selectbox(
        "Model Size",
        ["tiny", "base", "small", "medium"],
        index=1,
    )

    if st.button("Load Model", type="primary"):
        with st.spinner(f"Loading {model_size} model..."):
            st.session_state.transcriber = TranscriptionEngine(model_size)
            st.session_state.transcriber.load_model()
            st.success("Model loaded")

    tts_lang = st.selectbox(
        "TTS Language",
        ["en", "es", "fr", "de", "hi", "ja"],
        index=0,
    )


tab1, tab2, tab3, tab4 = st.tabs(["Record", "Upload", "Summary", "Export"])


with tab1:
    st.subheader("Live Recording")

    duration = st.slider("Recording duration (seconds)", 5, 60, 30)
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start Recording", type="primary", use_container_width=True):
            recorder = AudioRecorder()
            with st.spinner(f"Recording for {duration} seconds... Speak now"):
                try:
                    audio, _sr = recorder.record(duration)
                    filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                    saved_path = recorder.save_to_file(audio, filename)
                    st.session_state.recorded_file = saved_path
                    st.session_state.recording_complete = True
                    st.success(f"Recording complete. Saved as {filename}")
                except Exception as exc:
                    st.error(f"Recording failed: {exc}")

    with col2:
        if st.button("Clear Recording", use_container_width=True):
            if (
                st.session_state.recorded_file
                and os.path.exists(st.session_state.recorded_file)
            ):
                os.remove(st.session_state.recorded_file)
            st.session_state.recording_complete = False
            st.session_state.recorded_file = None
            st.session_state.transcription = ""
            st.rerun()

    if st.session_state.recording_complete and st.session_state.recorded_file:
        st.audio(st.session_state.recorded_file)

        if st.button("Transcribe Recording", type="secondary", use_container_width=True):
            if st.session_state.transcriber:
                with st.spinner("Transcribing audio... This may take a moment"):
                    try:
                        if os.path.exists(st.session_state.recorded_file):
                            result = st.session_state.transcriber.transcribe_file(
                                st.session_state.recorded_file
                            )
                            st.session_state.transcription = result["text"]
                            st.success("Transcription complete")

                            with st.expander("View transcription preview"):
                                preview = st.session_state.transcription
                                st.write(
                                    preview[:500] + "..."
                                    if len(preview) > 500
                                    else preview
                                )
                        else:
                            st.error("Recording file not found. Please record again.")
                    except Exception as exc:
                        st.error(f"Transcription failed: {exc}")
            else:
                st.error("Please load a model first from the sidebar.")


with tab2:
    st.subheader("Upload Audio File")

    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=["mp3", "wav", "m4a", "ogg"],
    )

    if uploaded_file:
        st.audio(uploaded_file)

        if st.button("Transcribe Uploaded", type="primary"):
            if st.session_state.transcriber:
                with st.spinner("Transcribing uploaded file..."):
                    try:
                        result = st.session_state.transcriber.transcribe_uploaded(
                            uploaded_file
                        )
                        st.session_state.transcription = result["text"]
                        st.success("Transcription complete")
                    except Exception as exc:
                        st.error(f"Transcription failed: {exc}")
            else:
                st.error("Please load a model first from the sidebar.")


with tab3:
    if st.session_state.transcription:
        word_count = len(st.session_state.transcription.split())
        st.info(f"Transcription: {word_count} words")

        with st.expander("View full transcription"):
            st.write(st.session_state.transcription)

        col1, col2 = st.columns([1.2, 1], vertical_alignment="bottom")
        with col1:
            style = st.selectbox(
                "Summary type",
                ["detailed", "action_only"],
                format_func=lambda value: (
                    "Detailed Summary" if value == "detailed" else "Action Items Only"
                ),
            )
        with col2:
            st.markdown(
                "<div style='height: 28px;'></div>",
                unsafe_allow_html=True,
            )
            if st.button("Generate Summary", type="primary", use_container_width=True):
                spinner_text = (
                    "Analyzing with AI..."
                    if st.session_state.summarizer.use_ai
                    else "Analyzing..."
                )
                with st.spinner(spinner_text):
                    st.session_state.summary = st.session_state.summarizer.generate_summary(
                        st.session_state.transcription, style
                    )
                    st.success("Summary generated")

        if st.session_state.summary:
            st.divider()

            if st.session_state.summary.get("summary"):
                st.markdown("### Summary")
                st.markdown(
                    f"""
                    <div style="
                        padding: 15px;
                        background-color: #f0f2f6;
                        color: #111827;
                        border-radius: 10px;
                        border-left: 4px solid #1E3A8A;
                        font-size: 16px;
                        line-height: 1.6;
                        margin: 10px 0;
                    ">
                        {st.session_state.summary['summary']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            content_col1, content_col2 = st.columns(2, gap="large")

            with content_col1:
                if st.session_state.summary.get("key_points"):
                    st.markdown("### Key Moments")
                    for index, point in enumerate(st.session_state.summary["key_points"], 1):
                        if point:
                            st.markdown(f"{index}. {point}")

                if st.session_state.summary.get("deadlines"):
                    st.markdown("### Deadlines")
                    for deadline in st.session_state.summary["deadlines"]:
                        if deadline:
                            st.markdown(f"- {deadline}")

            with content_col2:
                if st.session_state.summary.get("action_items"):
                    st.markdown("### Action Items")
                    for index, action in enumerate(
                        st.session_state.summary["action_items"], 1
                    ):
                        if action:
                            st.markdown(f"**{index}.** {action}")

                if st.session_state.summary.get("decisions"):
                    st.markdown("### Decisions")
                    for decision in st.session_state.summary["decisions"]:
                        if decision:
                            st.markdown(f"- {decision}")

            audio_col1, audio_col2 = st.columns([1, 1])
            with audio_col1:
                if st.button("Listen to Summary", use_container_width=True):
                    tts = TTSEngine(tts_lang)
                    text_to_speak = f"Summary: {st.session_state.summary.get('summary', '')}. "
                    if st.session_state.summary.get("action_items"):
                        text_to_speak += "Action items: " + ". ".join(
                            st.session_state.summary.get("action_items", [])
                        )

                    with st.spinner("Generating audio..."):
                        audio_file = tts.text_to_speech(text_to_speak[:500])
                        if audio_file:
                            st.audio(audio_file)
                            import time

                            time.sleep(2)
                            tts.cleanup(audio_file)
    else:
        st.info("No transcription yet. Record or upload audio first.")


with tab4:
    if st.session_state.transcription:
        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "Download Transcription",
                st.session_state.transcription,
                file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        if st.session_state.summary:
            with col2:
                content_type = st.session_state.summary.get("content_type", "general")
                summary_text = f"""# Voice Note Summary
Generated: {'OpenAI AI' if st.session_state.summarizer.use_ai else 'Local Analyzer'}
Content Type: {content_type.capitalize()}

## Summary
{st.session_state.summary.get('summary', 'No summary')}

## Key Moments
{chr(10).join(f"{i + 1}. {p}" for i, p in enumerate(st.session_state.summary.get('key_points', [])) if p)}

## Action Items
{chr(10).join(f"- {a}" for a in st.session_state.summary.get('action_items', []) if a)}

## Deadlines
{chr(10).join(f"- {d}" for d in st.session_state.summary.get('deadlines', []) if d)}

## Decisions
{chr(10).join(f"- {d}" for d in st.session_state.summary.get('decisions', []) if d)}

---
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
                st.download_button(
                    "Download Summary",
                    summary_text,
                    file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
    else:
        st.info("Nothing to export yet")


st.markdown("---")
st.caption("AI Voice Note Pro | Intelligent Summarizer for stories, meetings, actions, and notes")
