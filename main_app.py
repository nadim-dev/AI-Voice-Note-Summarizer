"""Main Streamlit application for Voice Note Summarizer"""

import sys
import os
from pathlib import Path
from datetime import datetime  # For timestamps

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from src.core.transcribe import TranscriptionEngine
from src.core.summarize import SummaryEngine
from src.core.tts_engine import TTSEngine
from src.core.audio_recorder import AudioRecorder

# Page config
st.set_page_config(
    page_title="AI Voice Note Pro",
    page_icon="🎤",
    layout="wide"
)

# Initialize session state
if 'transcription' not in st.session_state:
    st.session_state.transcription = ""
if 'summary' not in st.session_state:
    st.session_state.summary = {}
if 'action_items' not in st.session_state:
    st.session_state.action_items = []
if 'transcriber' not in st.session_state:
    st.session_state.transcriber = None
if 'summarizer' not in st.session_state:
    # Auto-load summarizer (reads API key from .env)
    st.session_state.summarizer = SummaryEngine()
if 'recording_complete' not in st.session_state:
    st.session_state.recording_complete = False
if 'recorded_file' not in st.session_state:
    st.session_state.recorded_file = None

# Title
st.title("🎤 AI Voice Note Pro")
st.markdown("### Record • Upload • Transcribe • Summarize")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Show AI status
    if st.session_state.summarizer.use_ai:
        st.success("✅ AI Mode: OpenAI Connected")
    else:
        st.warning("⚠️ Local Mode: Add OPENAI_API_KEY to .env for AI summaries")
    
    model_size = st.selectbox(
        "Model Size",
        ["tiny", "base", "small", "medium"],
        index=1
    )
    
    if st.button("🚀 Load Model", type="primary"):
        with st.spinner(f"Loading {model_size} model..."):
            st.session_state.transcriber = TranscriptionEngine(model_size)
            st.session_state.transcriber.load_model()
            st.success("✅ Model loaded!")
    
    tts_lang = st.selectbox(
        "TTS Language",
        ["en", "es", "fr", "de", "hi", "ja"],
        index=0
    )

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎙️ Record", "📤 Upload", "📝 Summary", "💾 Export"])

# Tab 1: Recording
with tab1:
    st.subheader("Live Recording")
    
    duration = st.slider("Recording duration (seconds)", 5, 60, 30)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔴 Start Recording", type="primary", use_container_width=True):
            recorder = AudioRecorder()
            with st.spinner(f"🎙️ Recording for {duration} seconds... Speak now!"):
                try:
                    audio, sr = recorder.record(duration)
                    # Save with unique filename
                    filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                    saved_path = recorder.save_to_file(audio, filename)
                    
                    # Store in session state
                    st.session_state.recorded_file = saved_path
                    st.session_state.recording_complete = True
                    st.success(f"✅ Recording complete! Saved as {filename}")
                except Exception as e:
                    st.error(f"Recording failed: {e}")
    
    with col2:
        if st.button("🗑️ Clear Recording", use_container_width=True):
            # Clean up file if exists
            if st.session_state.recorded_file and os.path.exists(st.session_state.recorded_file):
                os.remove(st.session_state.recorded_file)
            st.session_state.recording_complete = False
            st.session_state.recorded_file = None
            st.session_state.transcription = ""
            st.rerun()
    
    # Show recorded audio if available
    if st.session_state.recording_complete and st.session_state.recorded_file:
        st.audio(st.session_state.recorded_file)
        
        # Transcription button
        if st.button("📝 Transcribe Recording", type="secondary", use_container_width=True):
            if st.session_state.transcriber:
                with st.spinner("🔄 Transcribing audio... This may take a moment"):
                    try:
                        # Check if file exists
                        if os.path.exists(st.session_state.recorded_file):
                            result = st.session_state.transcriber.transcribe_file(st.session_state.recorded_file)
                            st.session_state.transcription = result['text']
                            st.success("✅ Transcription complete!")
                            
                            # Show preview
                            with st.expander("View transcription preview"):
                                st.write(st.session_state.transcription[:500] + "..." if len(st.session_state.transcription) > 500 else st.session_state.transcription)
                        else:
                            st.error("❌ Recording file not found. Please record again.")
                    except Exception as e:
                        st.error(f"❌ Transcription failed: {e}")
            else:
                st.error("⚠️ Please load a model first from the sidebar!")

# Tab 2: Upload
with tab2:
    st.subheader("Upload Audio File")
    
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=['mp3', 'wav', 'm4a', 'ogg']
    )
    
    if uploaded_file:
        st.audio(uploaded_file)
        
        if st.button("📝 Transcribe Uploaded", type="primary"):
            if st.session_state.transcriber:
                with st.spinner("🔄 Transcribing uploaded file..."):
                    try:
                        result = st.session_state.transcriber.transcribe_uploaded(uploaded_file)
                        st.session_state.transcription = result['text']
                        st.success("✅ Transcription complete!")
                    except Exception as e:
                        st.error(f"❌ Transcription failed: {e}")
            else:
                st.error("⚠️ Please load a model first from the sidebar!")

# Tab 3: Summary
with tab3:
    if st.session_state.transcription:
        # Show word count
        word_count = len(st.session_state.transcription.split())
        st.info(f"📝 Transcription: {word_count} words")
        
        with st.expander("View full transcription"):
            st.write(st.session_state.transcription)
        
        col1, col2 = st.columns(2)
        with col1:
            style = st.selectbox(
                "Summary type",
                ["detailed", "action_only"],
                format_func=lambda x: "📋 Detailed Summary" if x == "detailed" else "✅ Action Items Only"
            )
        with col2:
            if st.button("✨ Generate Summary", type="primary", use_container_width=True):
                with st.spinner("Analyzing with AI..." if st.session_state.summarizer.use_ai else "Analyzing..."):
                    summary = st.session_state.summarizer.generate_summary(
                        st.session_state.transcription, style
                    )
                    st.session_state.summary = summary
                    st.success("✅ Summary generated!")
        
        # Display summary
        if st.session_state.summary:
            st.divider()
            
            # Show which mode was used
            col1, col2 = st.columns(2)
            with col1:
                if st.session_state.summarizer.use_ai:
                    st.caption("🤖 Generated with OpenAI AI")
                else:
                    st.caption("📊 Generated with local analyzer")
            
            # Show content type if detected
            with col2:
                if 'content_type' in st.session_state.summary:
                    content_type = st.session_state.summary['content_type']
                    type_icons = {
                        'story': '📖',
                        'meeting': '👥',
                        'action': '✅',
                        'general': '📝',
                        'unknown': '❓'
                    }
                    icon = type_icons.get(content_type, '📄')
                    st.caption(f"{icon} Detected as: {content_type.capitalize()} content")
            
            if st.session_state.summary.get('summary'):
                st.markdown("### 📋 Summary")
                # Create a nice styled box for summary
                st.markdown(f"""
                <div style="
                    padding: 15px;
                    background-color: #f0f2f6;
                    border-radius: 10px;
                    border-left: 4px solid #1E3A8A;
                    font-size: 16px;
                    line-height: 1.6;
                    margin: 10px 0;
                ">
                    {st.session_state.summary['summary']}
                </div>
                """, unsafe_allow_html=True)
            
            if st.session_state.summary.get('key_points'):
                st.markdown("### 🔑 Key Moments")
                for i, point in enumerate(st.session_state.summary['key_points'], 1):
                    if point:
                        st.markdown(f"{i}. {point}")
            
            if st.session_state.summary.get('action_items'):
                st.markdown("### ✅ Action Items")
                for i, action in enumerate(st.session_state.summary['action_items'], 1):
                    if action:
                        st.markdown(f"**{i}.** {action}")
            
            if st.session_state.summary.get('deadlines'):
                st.markdown("### ⏰ Deadlines")
                for deadline in st.session_state.summary['deadlines']:
                    if deadline:
                        st.markdown(f"📅 {deadline}")
            
            if st.session_state.summary.get('decisions'):
                st.markdown("### ⚖️ Decisions")
                for decision in st.session_state.summary['decisions']:
                    if decision:
                        st.markdown(f"✓ {decision}")
            
            # TTS for summary
            if st.button("🔊 Listen to Summary"):
                tts = TTSEngine(tts_lang)
                # Create a nice spoken version
                text_to_speak = f"Summary: {st.session_state.summary.get('summary', '')}. "
                if st.session_state.summary.get('action_items'):
                    text_to_speak += "Action items: " + ". ".join(st.session_state.summary.get('action_items', []))
                
                with st.spinner("Generating audio..."):
                    audio_file = tts.text_to_speech(text_to_speak[:500])
                    if audio_file:
                        st.audio(audio_file)
                        # Clean up after playing
                        import time
                        time.sleep(2)
                        tts.cleanup(audio_file)
    else:
        st.info("👈 No transcription yet. Record or upload audio first.")

# Tab 4: Export
with tab4:
    if st.session_state.transcription:
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                "📥 Download Transcription",
                st.session_state.transcription,
                file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        if st.session_state.summary:
            with col2:
                # Get content type for export
                content_type = st.session_state.summary.get('content_type', 'general')
                type_icon = {
                    'story': '📖',
                    'meeting': '👥', 
                    'action': '✅',
                    'general': '📝'
                }.get(content_type, '📄')
                
                # Create formatted summary
                summary_text = f"""# Voice Note Summary {type_icon}
Generated: {'🤖 OpenAI AI' if st.session_state.summarizer.use_ai else '📊 Local Analyzer'}
Content Type: {content_type.capitalize()}

## Summary
{st.session_state.summary.get('summary', 'No summary')}

## Key Moments
{chr(10).join(f"{i+1}. {p}" for i, p in enumerate(st.session_state.summary.get('key_points', [])) if p)}

## Action Items
{chr(10).join(f"• {a}" for a in st.session_state.summary.get('action_items', []) if a)}

## Deadlines
{chr(10).join(f"⏰ {d}" for d in st.session_state.summary.get('deadlines', []) if d)}

## Decisions
{chr(10).join(f"✓ {d}" for d in st.session_state.summary.get('decisions', []) if d)}

---
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
                st.download_button(
                    "📥 Download Summary",
                    summary_text,
                    file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
    else:
        st.info("Nothing to export yet")

# Footer
st.markdown("---")
st.caption("🎤 AI Voice Note Pro | Intelligent Summarizer for Stories • Meetings • Actions • Notes")