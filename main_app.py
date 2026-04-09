"""Main Streamlit application for Voice Note Summarizer."""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.core.audio_recorder import AudioRecorder
from src.core.document_reader import DocumentReader
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


TTS_LANGUAGE_OPTIONS = {
    "English": "en",
    "Hindi": "hi",
    "Marathi": "mr",
    "Tamil": "ta",
    "Urdu": "ur",
}

VOICE_TONE_OPTIONS = {
    "Professional": "professional",
    "Friendly": "friendly",
    "Warm": "warm",
}

VOICE_ACCENT_OPTIONS = {
    "Global": "com",
    "India": "co.in",
    "UK": "co.uk",
    "Australia": "com.au",
}


def cleanup_generated_audio():
    audio_file = st.session_state.get("generated_audio_file")
    if audio_file and os.path.exists(audio_file):
        TTSEngine().cleanup(audio_file)
    st.session_state.generated_audio_file = None
    st.session_state.generated_audio_bytes = None
    st.session_state.generated_audio_name = None
    st.session_state.spoken_summary_text = ""


def build_spoken_summary(summary_data, tone):
    summary_text = summary_data.get("summary", "").strip()

    intro_map = {
        "professional": "Here is your voice note summary.",
        "friendly": "Here is a quick, easy summary of your voice note.",
        "warm": "Here is a warm and clear recap of your voice note.",
    }
    closing_map = {
        "professional": "That is the complete summary.",
        "friendly": "That is the full update in a simple way.",
        "warm": "That is your recap, shared in a more human way.",
    }

    if summary_text:
        return " ".join(
            [
                intro_map.get(tone, intro_map["professional"]),
                summary_text,
                closing_map.get(tone, closing_map["professional"]),
            ]
        )[:500]

    return intro_map.get(tone, intro_map["professional"])


def normalize_transcription_for_selected_language(transcription_text, target_language):
    normalized_result = st.session_state.summarizer.normalize_transcript(
        transcription_text,
        target_language=target_language,
    )
    return normalized_result.get("text", transcription_text)


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
if "generated_audio_file" not in st.session_state:
    st.session_state.generated_audio_file = None
if "generated_audio_bytes" not in st.session_state:
    st.session_state.generated_audio_bytes = None
if "generated_audio_name" not in st.session_state:
    st.session_state.generated_audio_name = None
if "spoken_summary_text" not in st.session_state:
    st.session_state.spoken_summary_text = ""
if "last_recording_message" not in st.session_state:
    st.session_state.last_recording_message = ""
if "recording_session" not in st.session_state:
    st.session_state.recording_session = None


def finalize_recording_session(tts_lang, model_size):
    session = st.session_state.recording_session
    if session is None or not session.is_finished():
        return

    if session.canceled:
        st.session_state.last_recording_message = "Recording cancelled"
        st.session_state.recording_session = None
        st.session_state.recording_complete = False
        return

    if session.error:
        st.session_state.last_recording_message = ""
        st.session_state.recording_session = None
        st.error(f"Recording failed: {session.error}")
        return

    try:
        if (
            st.session_state.transcriber is None
            or st.session_state.transcriber.model_size != model_size
        ):
            st.session_state.transcriber = TranscriptionEngine(model_size)
            st.session_state.transcriber.load_model()

        recorder = AudioRecorder()
        filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        saved_path = recorder.save_to_file(session.audio, filename)
        st.session_state.recorded_file = saved_path
        st.session_state.recording_complete = True
        st.session_state.last_recording_message = (
            f"Recording complete and saved as {filename}"
        )

        result = st.session_state.transcriber.transcribe_file(saved_path)
        st.session_state.transcription = normalize_transcription_for_selected_language(
            result["text"],
            tts_lang,
        )
    except Exception as exc:
        st.session_state.last_recording_message = ""
        st.error(f"Recording failed: {exc}")
    finally:
        st.session_state.recording_session = None


st.title("AI Voice Note Pro")
st.markdown("### Record • Upload • Transcribe • Summarize")


with st.sidebar:
    st.header("Settings")

    if st.session_state.summarizer.use_ai:
        pass
    else:
        st.warning("Local Mode: Add OPENAI_API_KEY or GROQ_API_KEY to .env for AI summaries")

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

    tts_language_name = st.selectbox(
        "TTS Language",
        list(TTS_LANGUAGE_OPTIONS.keys()),
        index=0,
    )
    tts_lang = TTS_LANGUAGE_OPTIONS[tts_language_name]

    voice_tone_name = st.selectbox(
        "Voice Style",
        list(VOICE_TONE_OPTIONS.keys()),
        index=2,
    )
    voice_tone = VOICE_TONE_OPTIONS[voice_tone_name]

    voice_accent_name = st.selectbox(
        "Voice Accent",
        list(VOICE_ACCENT_OPTIONS.keys()),
        index=1,
    )
    voice_accent = VOICE_ACCENT_OPTIONS[voice_accent_name]

    voice_speed = st.selectbox(
        "Voice Speed",
        ["Natural", "Slow and clear"],
        index=0,
    )
    voice_is_slow = voice_speed == "Slow and clear"


tab1, tab2, tab3, tab4 = st.tabs(["Record", "Upload", "Summary", "Export"])


with tab1:
    st.subheader("Live Recording")
    finalize_recording_session(tts_lang, model_size)
    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.recording_session is None and st.button(
            "Start Recording", type="primary", use_container_width=True
        ):
            recorder = AudioRecorder()
            st.session_state.last_recording_message = ""
            st.session_state.recording_complete = False
            st.session_state.recording_session = recorder.start_recording_session()
            st.rerun()

    with col2:
        if st.session_state.recording_session is None and st.button(
            "Clear Recording", use_container_width=True
        ):
            if (
                st.session_state.recorded_file
                and os.path.exists(st.session_state.recorded_file)
            ):
                os.remove(st.session_state.recorded_file)
            st.session_state.recording_complete = False
            st.session_state.recorded_file = None
            st.session_state.transcription = ""
            st.session_state.summary = {}
            st.session_state.last_recording_message = ""
            st.rerun()

    active_session = st.session_state.recording_session
    if active_session is not None:
        st.markdown(
            """
            <div style="
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 16px;
                padding: 18px 20px;
                margin: 18px 0;
                background: linear-gradient(135deg, rgba(255,82,82,0.16), rgba(255,255,255,0.03));
            ">
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
                    <div style="
                        width:14px;
                        height:14px;
                        border-radius:999px;
                        background:#ff5252;
                        box-shadow:0 0 0 0 rgba(255,82,82,0.7);
                        animation:pulse-record 1.4s infinite;
                    "></div>
                    <div style="font-size:28px; font-weight:700; color:#ffffff;">Recording in progress</div>
                </div>
                <div style="font-size:16px; color:#f3f4f6;">
                    Speak naturally. We will stop when you pause, or you can stop or cancel below.
                </div>
            </div>
            <style>
                @keyframes pulse-record {
                    0% { box-shadow: 0 0 0 0 rgba(255,82,82,0.7); }
                    70% { box-shadow: 0 0 0 12px rgba(255,82,82,0); }
                    100% { box-shadow: 0 0 0 0 rgba(255,82,82,0); }
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("Stop Recording", type="primary", use_container_width=True):
                active_session.stop()
                st.rerun()
        with action_col2:
            if st.button("Cancel Recording", use_container_width=True):
                active_session.cancel()
                st.rerun()

        time.sleep(0.5)
        st.rerun()
    else:
        st.caption("Speak naturally. Recording starts immediately and stops once you pause.")

    if st.session_state.last_recording_message:
        st.success(st.session_state.last_recording_message)

    if st.session_state.recording_complete and st.session_state.recorded_file:
        st.audio(st.session_state.recorded_file)

        if st.session_state.transcription:
            with st.expander("View transcription preview"):
                preview = st.session_state.transcription
                st.write(
                    preview[:500] + "..."
                    if len(preview) > 500
                    else preview
                )


with tab2:
    st.subheader("Upload Audio Or Document")

    uploaded_file = st.file_uploader(
        "Choose an audio or document file",
        type=["mp3", "wav", "m4a", "ogg", "txt", "pdf"],
    )

    if uploaded_file:
        uploaded_extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
        is_audio_file = uploaded_extension in {"mp3", "wav", "m4a", "ogg"}

        if is_audio_file:
            st.audio(uploaded_file)

        button_label = "Transcribe Uploaded Audio" if is_audio_file else "Extract Document Text"

        if st.button(button_label, type="primary"):
            if is_audio_file:
                if st.session_state.transcriber:
                    with st.spinner("Transcribing uploaded audio..."):
                        try:
                            result = st.session_state.transcriber.transcribe_uploaded(
                                uploaded_file
                            )
                            st.session_state.transcription = (
                                normalize_transcription_for_selected_language(
                                    result["text"],
                                    tts_lang,
                                )
                            )
                            st.success("Transcription complete")
                        except Exception as exc:
                            st.error(f"Transcription failed: {exc}")
                else:
                    st.error("Please load a model first from the sidebar.")
            else:
                with st.spinner("Reading document..."):
                    try:
                        document_reader = DocumentReader()
                        extracted_text = document_reader.read_uploaded_file(uploaded_file)
                        if not extracted_text:
                            st.error("No readable text was found in the document.")
                        else:
                            st.session_state.transcription = extracted_text
                            st.success("Document text extracted")
                    except Exception as exc:
                        st.error(f"Document processing failed: {exc}")


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
                    cleanup_generated_audio()
                    st.session_state.summary = st.session_state.summarizer.generate_summary(
                        st.session_state.transcription,
                        style,
                        target_language=tts_lang,
                    )
                    st.success("Summary generated")

        if st.session_state.summary:
            st.divider()

            summary_provider = st.session_state.summary.get("ai_provider", "local")
            summary_model = st.session_state.summary.get("ai_model", "local")
            summary_ai_used = st.session_state.summary.get("ai_used", False)
            fallback_reason = st.session_state.summary.get("fallback_reason", "")

            if summary_ai_used:
                st.caption(
                    f"Summary generated with {summary_provider.capitalize()} ({summary_model})"
                )
            elif fallback_reason:
                st.warning(
                    f"AI summary unavailable, local summary used instead. Reason: {fallback_reason}"
                )

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
                if st.button("Generate Human-Like Voice", use_container_width=True):
                    cleanup_generated_audio()
                    tts = TTSEngine(
                        lang=tts_lang,
                        tld=voice_accent,
                        slow=voice_is_slow,
                    )
                    spoken_summary = build_spoken_summary(
                        st.session_state.summary,
                        voice_tone,
                    )
                    with st.spinner("Generating audio..."):
                        audio_file = tts.text_to_speech(spoken_summary)
                        if audio_file:
                            audio_bytes = tts.read_audio_bytes(audio_file)
                            if audio_bytes:
                                st.session_state.generated_audio_file = audio_file
                                st.session_state.generated_audio_bytes = audio_bytes
                                st.session_state.generated_audio_name = (
                                    f"voice_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                                )
                                st.session_state.spoken_summary_text = spoken_summary
                                st.success("Voice summary ready")
                            else:
                                tts.cleanup(audio_file)
                                st.error("Audio was created but could not be loaded.")
                        else:
                            st.error("Could not generate voice summary.")
            with audio_col2:
                if st.session_state.generated_audio_bytes:
                    st.download_button(
                        "Download Voice Summary",
                        data=st.session_state.generated_audio_bytes,
                        file_name=st.session_state.generated_audio_name,
                        mime="audio/mpeg",
                        use_container_width=True,
                    )

            if st.session_state.generated_audio_bytes:
                st.markdown("### Voice Summary")
                st.audio(st.session_state.generated_audio_bytes, format="audio/mp3")
                with st.expander("Voice script preview"):
                    st.write(st.session_state.spoken_summary_text)
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
