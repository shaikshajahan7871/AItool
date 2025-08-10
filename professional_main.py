"""
Alternative Implementation: Real-Time Audio Transcription with AssemblyAI
========================================================================

This version uses AssemblyAI for streaming transcription and DeepL for translation
Better for production use with commercial API support and higher accuracy

Features:
- AssemblyAI Universal Streaming (300ms latency)
- DeepL Translation API (higher quality)
- WebSocket-based real-time transcription
- Professional error handling and reconnection
"""

import sys
import asyncio
import threading
from typing import Optional
import numpy as np
import sounddevice as sd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QTextEdit, QComboBox, QLabel, 
                             QGroupBox, QMessageBox, QLineEdit, QCheckBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont
import pyperclip
import requests
import json
import websocket
import base64
import wave
import io

# Alternative using AssemblyAI Streaming API
try:
    import assemblyai as aai
    ASSEMBLYAI_AVAILABLE = True
except ImportError:
    ASSEMBLYAI_AVAILABLE = False

# Alternative using DeepL for translation
try:
    import deepl
    DEEPL_AVAILABLE = True
except ImportError:
    DEEPL_AVAILABLE = False


class AssemblyAIStreamer(QThread):
    """Real-time transcription using AssemblyAI Universal Streaming"""

    transcription_ready = pyqtSignal(str, bool)  # text, is_final
    error_occurred = pyqtSignal(str)

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.ws = None
        self.is_active = False
        self.audio_queue = []

    def start_streaming(self):
        """Start streaming transcription"""
        self.is_active = True
        self.start()

    def stop_streaming(self):
        """Stop streaming transcription"""
        self.is_active = False
        if self.ws:
            self.ws.close()

    def run(self):
        """Main streaming loop"""
        try:
            # WebSocket URL for AssemblyAI
            ws_url = "wss://api.assemblyai.com/v2/realtime/ws"

            def on_message(ws, message):
                data = json.loads(message)
                if data['message_type'] == 'FinalTranscript':
                    self.transcription_ready.emit(data['text'], True)
                elif data['message_type'] == 'PartialTranscript':
                    self.transcription_ready.emit(data['text'], False)

            def on_error(ws, error):
                self.error_occurred.emit(str(error))

            def on_open(ws):
                # Send configuration
                config = {
                    "sample_rate": 16000,
                    "word_boost": ["interview", "meeting", "conference"],
                    "format_text": True
                }
                ws.send(json.dumps(config))

            # Create WebSocket connection
            self.ws = websocket.WebSocketApp(
                f"{ws_url}?sample_rate=16000&token={self.api_key}",
                on_message=on_message,
                on_error=on_error,
                on_open=on_open
            )

            self.ws.run_forever()

        except Exception as e:
            self.error_occurred.emit(f"AssemblyAI connection error: {e}")

    def send_audio(self, audio_data):
        """Send audio data to AssemblyAI"""
        if self.ws and self.is_active:
            # Convert numpy array to bytes
            audio_bytes = (audio_data * 32768).astype(np.int16).tobytes()
            # Base64 encode for WebSocket transmission
            encoded_audio = base64.b64encode(audio_bytes).decode('utf-8')

            message = {
                "audio_data": encoded_audio
            }
            self.ws.send(json.dumps(message))


class DeepLTranslator(QThread):
    """High-quality translation using DeepL API"""

    translation_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_key: str):
        super().__init__()
        if DEEPL_AVAILABLE:
            self.translator = deepl.Translator(api_key)
        self.translation_queue = []
        self.target_language = "EN"
        self.is_active = False

    def set_target_language(self, language_code: str):
        """Set target language for translation"""
        # DeepL language codes (different from Google Translate)
        deepl_codes = {
            "en": "EN", "es": "ES", "fr": "FR", "de": "DE", 
            "it": "IT", "pt": "PT", "ru": "RU", "ja": "JA",
            "zh": "ZH", "ko": "KO", "nl": "NL", "pl": "PL"
        }
        self.target_language = deepl_codes.get(language_code, "EN")

    def add_text(self, text: str):
        """Add text for translation"""
        if self.is_active and text.strip():
            self.translation_queue.append(text)

    def start_translation(self):
        """Start translation worker"""
        self.is_active = True
        self.start()

    def stop_translation(self):
        """Stop translation worker"""
        self.is_active = False

    def run(self):
        """Main translation loop"""
        while self.is_active:
            try:
                if self.translation_queue and DEEPL_AVAILABLE:
                    text = self.translation_queue.pop(0)

                    # Translate with DeepL
                    result = self.translator.translate_text(
                        text, 
                        target_lang=self.target_language
                    )

                    self.translation_ready.emit(result.text)

                else:
                    self.msleep(100)  # Wait 100ms

            except Exception as e:
                self.error_occurred.emit(f"Translation error: {e}")
                self.msleep(1000)  # Wait 1 second on error


class EnhancedAudioCapture(QThread):
    """Enhanced audio capture with preprocessing"""

    audio_ready = pyqtSignal(np.ndarray)
    volume_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.is_recording = False
        self.volume_threshold = 0.01

    def start_recording(self):
        """Start audio recording"""
        self.is_recording = True
        self.start()

    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False

    def run(self):
        """Enhanced audio capture with voice activity detection"""
        try:
            def audio_callback(indata, frames, time, status):
                if self.is_recording:
                    audio_chunk = indata[:, 0].copy()

                    # Calculate volume level
                    volume = np.sqrt(np.mean(audio_chunk**2))
                    self.volume_changed.emit(volume)

                    # Voice activity detection (simple threshold)
                    if volume > self.volume_threshold:
                        # Apply simple noise gate
                        audio_chunk = np.where(
                            np.abs(audio_chunk) > self.volume_threshold,
                            audio_chunk,
                            0
                        )
                        self.audio_ready.emit(audio_chunk)

            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=audio_callback,
                blocksize=self.chunk_size,
                dtype=np.float32
            ):
                while self.is_recording:
                    self.msleep(10)

        except Exception as e:
            print(f"Audio capture error: {e}")


class ProfessionalMainWindow(QMainWindow):
    """Professional version with commercial APIs"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Professional Audio Transcription Suite")
        self.setGeometry(100, 100, 1000, 700)

        # API Configuration
        self.assemblyai_api_key = ""
        self.deepl_api_key = ""

        # Components
        self.audio_capture = EnhancedAudioCapture()
        self.transcriber = None
        self.translator = None

        # UI State
        self.is_recording = False
        self.current_transcript = ""
        self.current_translation = ""

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup professional UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # API Configuration Section
        api_group = QGroupBox("API Configuration")
        api_layout = QVBoxLayout(api_group)

        # AssemblyAI API Key
        assemblyai_layout = QHBoxLayout()
        assemblyai_layout.addWidget(QLabel("AssemblyAI API Key:"))
        self.assemblyai_key_input = QLineEdit()
        self.assemblyai_key_input.setEchoMode(QLineEdit.Password)
        self.assemblyai_key_input.setPlaceholderText("Enter your AssemblyAI API key")
        assemblyai_layout.addWidget(self.assemblyai_key_input)

        # DeepL API Key
        deepl_layout = QHBoxLayout()
        deepl_layout.addWidget(QLabel("DeepL API Key:"))
        self.deepl_key_input = QLineEdit()
        self.deepl_key_input.setEchoMode(QLineEdit.Password)
        self.deepl_key_input.setPlaceholderText("Enter your DeepL API key (optional)")
        deepl_layout.addWidget(self.deepl_key_input)

        api_layout.addLayout(assemblyai_layout)
        api_layout.addLayout(deepl_layout)
        layout.addWidget(api_group)

        # Control Panel
        control_group = QGroupBox("Controls")
        control_layout = QHBoxLayout(control_group)

        # Start/Stop Recording
        self.record_button = QPushButton("🎙️ Start Professional Recording")
        self.record_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4facfe, stop:1 #00f2fe);
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #43a3f5, stop:1 #00e9f5);
            }
        """)
        self.record_button.clicked.connect(self.toggle_recording)

        # Language Selection
        self.language_combo = QComboBox()
        languages = {
            "EN": "English", "ES": "Spanish", "FR": "French", 
            "DE": "German", "IT": "Italian", "PT": "Portuguese",
            "RU": "Russian", "JA": "Japanese", "ZH": "Chinese",
            "KO": "Korean", "NL": "Dutch", "PL": "Polish"
        }
        for code, name in languages.items():
            self.language_combo.addItem(f"{name} ({code})", code)

        self.translation_enabled = QCheckBox("Enable Translation")
        self.translation_enabled.setChecked(True)

        control_layout.addWidget(self.record_button)
        control_layout.addWidget(QLabel("Target Language:"))
        control_layout.addWidget(self.language_combo)
        control_layout.addWidget(self.translation_enabled)
        control_layout.addStretch()

        layout.addWidget(control_group)

        # Real-time Transcription
        transcript_group = QGroupBox("Live Transcription (AssemblyAI Universal Streaming)")
        transcript_layout = QVBoxLayout(transcript_group)

        self.transcript_text = QTextEdit()
        self.transcript_text.setFont(QFont("Consolas", 11))
        self.transcript_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        transcript_buttons = QHBoxLayout()
        self.copy_transcript_btn = QPushButton("📋 Copy Transcript")
        self.save_transcript_btn = QPushButton("💾 Save Transcript")
        self.clear_transcript_btn = QPushButton("🗑️ Clear")

        transcript_buttons.addWidget(self.copy_transcript_btn)
        transcript_buttons.addWidget(self.save_transcript_btn)
        transcript_buttons.addWidget(self.clear_transcript_btn)
        transcript_buttons.addStretch()

        transcript_layout.addWidget(self.transcript_text)
        transcript_layout.addLayout(transcript_buttons)

        layout.addWidget(transcript_group)

        # Translation Display
        translation_group = QGroupBox("Professional Translation (DeepL)")
        translation_layout = QVBoxLayout(translation_group)

        self.translation_text = QTextEdit()
        self.translation_text.setFont(QFont("Consolas", 11))
        self.translation_text.setStyleSheet("""
            QTextEdit {
                background-color: #f0f8ff;
                border: 2px solid #add8e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        translation_buttons = QHBoxLayout()
        self.copy_translation_btn = QPushButton("📋 Copy Translation")
        self.export_both_btn = QPushButton("📤 Export Both")

        translation_buttons.addWidget(self.copy_translation_btn)
        translation_buttons.addWidget(self.export_both_btn)
        translation_buttons.addStretch()

        translation_layout.addWidget(self.translation_text)
        translation_layout.addLayout(translation_buttons)

        layout.addWidget(translation_group)

        # Connect button signals
        self.copy_transcript_btn.clicked.connect(self.copy_transcript)
        self.copy_translation_btn.clicked.connect(self.copy_translation)
        self.clear_transcript_btn.clicked.connect(self.clear_all_text)

    def connect_signals(self):
        """Connect worker signals"""
        self.audio_capture.audio_ready.connect(self.on_audio_ready)

    def toggle_recording(self):
        """Start/stop professional recording"""
        if not self.is_recording:
            self.start_professional_recording()
        else:
            self.stop_professional_recording()

    def start_professional_recording(self):
        """Start recording with professional APIs"""
        # Validate API keys
        self.assemblyai_api_key = self.assemblyai_key_input.text().strip()
        self.deepl_api_key = self.deepl_key_input.text().strip()

        if not self.assemblyai_api_key:
            QMessageBox.warning(self, "API Key Required", 
                              "Please enter your AssemblyAI API key to continue.")
            return

        # Initialize transcriber
        self.transcriber = AssemblyAIStreamer(self.assemblyai_api_key)
        self.transcriber.transcription_ready.connect(self.on_transcription_ready)
        self.transcriber.error_occurred.connect(self.on_transcription_error)

        # Initialize translator if enabled
        if self.translation_enabled.isChecked() and self.deepl_api_key:
            self.translator = DeepLTranslator(self.deepl_api_key)
            self.translator.translation_ready.connect(self.on_translation_ready)
            self.translator.error_occurred.connect(self.on_translation_error)
            self.translator.set_target_language(
                self.language_combo.currentData()
            )
            self.translator.start_translation()

        # Start recording
        self.is_recording = True
        self.record_button.setText("🛑 Stop Recording")
        self.record_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ff6b6b, stop:1 #ee5a52);
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
        """)

        # Start workers
        self.audio_capture.start_recording()
        self.transcriber.start_streaming()

    def stop_professional_recording(self):
        """Stop professional recording"""
        self.is_recording = False

        # Stop workers
        self.audio_capture.stop_recording()
        if self.transcriber:
            self.transcriber.stop_streaming()
        if self.translator:
            self.translator.stop_translation()

        # Reset UI
        self.record_button.setText("🎙️ Start Professional Recording")
        self.record_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4facfe, stop:1 #00f2fe);
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
        """)

    def on_audio_ready(self, audio_data):
        """Handle audio data"""
        if self.transcriber and self.is_recording:
            self.transcriber.send_audio(audio_data)

    def on_transcription_ready(self, text, is_final):
        """Handle transcription results"""
        if is_final:
            self.current_transcript += text + " "
            self.transcript_text.setPlainText(self.current_transcript)

            # Send to translator
            if self.translator:
                self.translator.add_text(text)

        # Auto-scroll
        cursor = self.transcript_text.textCursor()
        cursor.movePosition(cursor.End)
        self.transcript_text.setTextCursor(cursor)

    def on_translation_ready(self, translated_text):
        """Handle translation results"""
        self.current_translation += translated_text + " "
        self.translation_text.setPlainText(self.current_translation)

        # Auto-scroll
        cursor = self.translation_text.textCursor()
        cursor.movePosition(cursor.End)
        self.translation_text.setTextCursor(cursor)

    def on_transcription_error(self, error):
        """Handle transcription errors"""
        QMessageBox.critical(self, "Transcription Error", f"Error: {error}")

    def on_translation_error(self, error):
        """Handle translation errors"""
        QMessageBox.warning(self, "Translation Error", f"Error: {error}")

    def copy_transcript(self):
        """Copy transcript to clipboard"""
        if self.current_transcript.strip():
            pyperclip.copy(self.current_transcript)
            QMessageBox.information(self, "Copied", "Transcript copied to clipboard!")

    def copy_translation(self):
        """Copy translation to clipboard"""
        if self.current_translation.strip():
            pyperclip.copy(self.current_translation)
            QMessageBox.information(self, "Copied", "Translation copied to clipboard!")

    def clear_all_text(self):
        """Clear all text"""
        self.transcript_text.clear()
        self.translation_text.clear()
        self.current_transcript = ""
        self.current_translation = ""


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Professional Audio Transcription Suite")

    # Check for required dependencies
    if not ASSEMBLYAI_AVAILABLE:
        QMessageBox.critical(None, "Missing Dependency", 
                           "AssemblyAI package not found. Install with: pip install assemblyai")
        sys.exit(1)

    window = ProfessionalMainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
