# Create a comprehensive implementation guide with code examples for both Python and JavaScript approaches

python_code_example = '''
# Python Implementation - Real-time Audio Transcription with Translation
import sounddevice as sd
import whisper
import numpy as np
import threading
import queue
from googletrans import Translator
import pyperclip
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QWidget, QPushButton, QTextEdit, 
                             QComboBox, QLabel)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
import sys
import io
from scipy.io import wavfile

class AudioRecorder(QThread):
    audio_ready = pyqtSignal(np.ndarray)
    
    def __init__(self, sample_rate=16000, chunk_size=1024):
        super().__init__()
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.recording = False
        self.audio_buffer = queue.Queue()
        
    def run(self):
        def audio_callback(indata, frames, time, status):
            if self.recording:
                self.audio_buffer.put(indata.copy())
        
        with sd.InputStream(callback=audio_callback, 
                          samplerate=self.sample_rate, 
                          channels=1):
            while self.recording:
                if not self.audio_buffer.empty():
                    audio_chunk = self.audio_buffer.get()
                    self.audio_ready.emit(audio_chunk.flatten())
                self.msleep(100)
    
    def start_recording(self):
        self.recording = True
        self.start()
    
    def stop_recording(self):
        self.recording = False
        self.wait()

class TranscriptionWorker(QThread):
    transcription_ready = pyqtSignal(str, str)  # original, translated
    
    def __init__(self, model_size="base"):
        super().__init__()
        self.model = whisper.load_model(model_size)
        self.translator = Translator()
        self.audio_queue = queue.Queue()
        self.target_language = 'en'
        self.running = False
        
    def add_audio(self, audio_data):
        self.audio_queue.put(audio_data)
    
    def set_target_language(self, lang_code):
        self.target_language = lang_code
        
    def run(self):
        self.running = True
        audio_buffer = []
        
        while self.running:
            try:
                # Collect audio chunks for 2 seconds
                chunk_count = 0
                while chunk_count < 32 and not self.audio_queue.empty():  # ~2 seconds at 16kHz
                    audio_buffer.extend(self.audio_queue.get(timeout=0.1))
                    chunk_count += 1
                
                if len(audio_buffer) > 16000:  # At least 1 second of audio
                    # Convert to numpy array and normalize
                    audio_array = np.array(audio_buffer[-32000:])  # Last 2 seconds
                    audio_array = audio_array.astype(np.float32)
                    audio_array = audio_array / np.max(np.abs(audio_array))
                    
                    # Transcribe with Whisper
                    result = self.model.transcribe(audio_array, language='auto')
                    text = result['text'].strip()
                    
                    if text and len(text) > 3:
                        # Translate if target language is not auto-detected language
                        translated_text = ""
                        if self.target_language != 'en':
                            try:
                                translation = self.translator.translate(text, dest=self.target_language)
                                translated_text = translation.text
                            except:
                                translated_text = "Translation failed"
                        
                        self.transcription_ready.emit(text, translated_text)
                    
                    # Keep some overlap for context
                    audio_buffer = audio_buffer[-8000:]  # Keep last 0.5 seconds
                
            except queue.Empty:
                self.msleep(50)
            except Exception as e:
                print(f"Transcription error: {e}")
                self.msleep(100)
    
    def stop(self):
        self.running = False
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-time Audio Transcription & Translation")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize components
        self.audio_recorder = AudioRecorder()
        self.transcription_worker = TranscriptionWorker()
        self.is_recording = False
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Record button
        self.record_btn = QPushButton("🎙️ Start Recording")
        self.record_btn.setFont(QFont("Arial", 12))
        self.record_btn.clicked.connect(self.toggle_recording)
        control_layout.addWidget(self.record_btn)
        
        # Language selection
        control_layout.addWidget(QLabel("Target Language:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            "English (en)", "Spanish (es)", "French (fr)", "German (de)",
            "Italian (it)", "Portuguese (pt)", "Russian (ru)", "Chinese (zh)",
            "Japanese (ja)", "Korean (ko)", "Arabic (ar)"
        ])
        self.language_combo.currentTextChanged.connect(self.change_language)
        control_layout.addWidget(self.language_combo)
        
        # Copy button
        self.copy_btn = QPushButton("📋 Copy Text")
        self.copy_btn.clicked.connect(self.copy_text)
        control_layout.addWidget(self.copy_btn)
        
        layout.addLayout(control_layout)
        
        # Transcription display
        layout.addWidget(QLabel("Live Transcription:"))
        self.transcription_text = QTextEdit()
        self.transcription_text.setFont(QFont("Arial", 11))
        self.transcription_text.setMaximumHeight(200)
        layout.addWidget(self.transcription_text)
        
        # Translation display
        layout.addWidget(QLabel("Translation:"))
        self.translation_text = QTextEdit()
        self.translation_text.setFont(QFont("Arial", 11))
        self.translation_text.setMaximumHeight(200)
        layout.addWidget(self.translation_text)
        
        # Status
        self.status_label = QLabel("Ready to record")
        layout.addWidget(self.status_label)
        
    def setup_connections(self):
        self.audio_recorder.audio_ready.connect(self.transcription_worker.add_audio)
        self.transcription_worker.transcription_ready.connect(self.update_transcription)
        
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        self.is_recording = True
        self.record_btn.setText("⏹️ Stop Recording")
        self.status_label.setText("Recording... Speak now!")
        
        self.transcription_worker.start()
        self.audio_recorder.start_recording()
        
    def stop_recording(self):
        self.is_recording = False
        self.record_btn.setText("🎙️ Start Recording")
        self.status_label.setText("Stopped recording")
        
        self.audio_recorder.stop_recording()
        self.transcription_worker.stop()
        
    def change_language(self, text):
        lang_code = text.split('(')[1].split(')')[0]
        self.transcription_worker.set_target_language(lang_code)
        
    def update_transcription(self, original, translated):
        # Update transcription
        current_text = self.transcription_text.toPlainText()
        new_text = current_text + "\\n" + original
        self.transcription_text.setPlainText(new_text[-1000:])  # Keep last 1000 chars
        self.transcription_text.moveCursor(self.transcription_text.textCursor().End)
        
        # Update translation
        if translated:
            current_trans = self.translation_text.toPlainText()
            new_trans = current_trans + "\\n" + translated
            self.translation_text.setPlainText(new_trans[-1000:])
            self.translation_text.moveCursor(self.translation_text.textCursor().End)
            
    def copy_text(self):
        text_to_copy = self.transcription_text.toPlainText()
        if self.translation_text.toPlainText():
            text_to_copy += "\\n\\nTranslation:\\n" + self.translation_text.toPlainText()
        pyperclip.copy(text_to_copy)
        self.status_label.setText("Text copied to clipboard!")
        
        # Reset status after 2 seconds
        QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
'''

javascript_code_example = '''
// JavaScript/Electron Implementation - Real-time Audio Transcription
// main.js (Electron Main Process)
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

function createWindow() {
    const mainWindow = new BrowserWindow({
        width: 1000,
        height: 700,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true
        }
    });

    mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// index.html
const html_content = `
<!DOCTYPE html>
<html>
<head>
    <title>Real-time Audio Transcription</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            align-items: center;
            flex-wrap: wrap;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
        }
        .record-btn {
            background-color: #28a745;
            color: white;
            font-size: 16px;
            padding: 12px 24px;
        }
        .record-btn:hover {
            background-color: #218838;
        }
        .record-btn.recording {
            background-color: #dc3545;
        }
        .copy-btn {
            background-color: #007bff;
            color: white;
        }
        .copy-btn:hover {
            background-color: #0056b3;
        }
        select {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .transcription-area {
            margin-bottom: 20px;
        }
        .transcription-area label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        .transcription-area textarea {
            width: 100%;
            height: 150px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            resize: vertical;
            font-family: monospace;
        }
        .status {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-weight: bold;
        }
        .status.ready { background-color: #d4edda; color: #155724; }
        .status.recording { background-color: #fff3cd; color: #856404; }
        .status.error { background-color: #f8d7da; color: #721c24; }
        .interim { opacity: 0.7; font-style: italic; }
        .final { opacity: 1; font-weight: normal; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Real-time Audio Transcription & Translation</h1>
        
        <div id="status" class="status ready">Ready to start recording</div>
        
        <div class="controls">
            <button id="recordBtn" class="record-btn">Start Recording</button>
            
            <label for="languageSelect">Target Language:</label>
            <select id="languageSelect">
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="it">Italian</option>
                <option value="pt">Portuguese</option>
                <option value="ru">Russian</option>
                <option value="zh">Chinese</option>
                <option value="ja">Japanese</option>
                <option value="ko">Korean</option>
                <option value="ar">Arabic</option>
            </select>
            
            <button id="copyBtn" class="copy-btn">📋 Copy Text</button>
        </div>
        
        <div class="transcription-area">
            <label for="transcriptionText">Live Transcription:</label>
            <textarea id="transcriptionText" readonly placeholder="Your speech will appear here..."></textarea>
        </div>
        
        <div class="transcription-area">
            <label for="translationText">Translation:</label>
            <textarea id="translationText" readonly placeholder="Translation will appear here..."></textarea>
        </div>
    </div>

    <script src="renderer.js"></script>
</body>
</html>
`;

// renderer.js (Electron Renderer Process)
const renderer_js = `
class AudioTranscriber {
    constructor() {
        this.isRecording = false;
        this.recognition = null;
        this.targetLanguage = 'en';
        
        this.initializeElements();
        this.setupSpeechRecognition();
        this.bindEvents();
    }
    
    initializeElements() {
        this.recordBtn = document.getElementById('recordBtn');
        this.copyBtn = document.getElementById('copyBtn');
        this.languageSelect = document.getElementById('languageSelect');
        this.transcriptionText = document.getElementById('transcriptionText');
        this.translationText = document.getElementById('translationText');
        this.status = document.getElementById('status');
    }
    
    setupSpeechRecognition() {
        // Check for Web Speech API support
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.showError('Web Speech API not supported in this browser');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure speech recognition
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        
        // Event handlers
        this.recognition.onstart = () => {
            this.updateStatus('Recording... Speak now!', 'recording');
        };
        
        this.recognition.onresult = (event) => {
            this.handleSpeechResult(event);
        };
        
        this.recognition.onerror = (event) => {
            this.showError('Speech recognition error: ' + event.error);
        };
        
        this.recognition.onend = () => {
            if (this.isRecording) {
                // Restart recognition if we're still supposed to be recording
                setTimeout(() => {
                    if (this.isRecording) {
                        this.recognition.start();
                    }
                }, 100);
            } else {
                this.updateStatus('Recording stopped', 'ready');
            }
        };
    }
    
    async handleSpeechResult(event) {
        let interimTranscript = '';
        let finalTranscript = this.transcriptionText.value;
        
        // Process all results
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
                
                // Translate if target language is different
                if (this.targetLanguage !== 'en') {
                    await this.translateText(transcript);
                }
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Update transcription display
        this.transcriptionText.value = finalTranscript;
        if (interimTranscript) {
            this.transcriptionText.value += interimTranscript;
        }
        
        // Auto-scroll to bottom
        this.transcriptionText.scrollTop = this.transcriptionText.scrollHeight;
    }
    
    async translateText(text) {
        try {
            // Using a simple Google Translate API approach
            // Note: In production, you'd want to use official APIs with proper authentication
            const response = await fetch(\`https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=\${this.targetLanguage}&dt=t&q=\${encodeURIComponent(text)}\`);
            const data = await response.json();
            
            if (data && data[0] && data[0][0]) {
                const translatedText = data[0][0][0];
                this.translationText.value += translatedText + ' ';
                this.translationText.scrollTop = this.translationText.scrollHeight;
            }
        } catch (error) {
            console.error('Translation error:', error);
            this.translationText.value += '[Translation failed] ';
        }
    }
    
    bindEvents() {
        this.recordBtn.addEventListener('click', () => {
            this.toggleRecording();
        });
        
        this.copyBtn.addEventListener('click', () => {
            this.copyToClipboard();
        });
        
        this.languageSelect.addEventListener('change', (e) => {
            this.targetLanguage = e.target.value;
        });
    }
    
    toggleRecording() {
        if (!this.recognition) {
            this.showError('Speech recognition not available');
            return;
        }
        
        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }
    
    startRecording() {
        this.isRecording = true;
        this.recordBtn.textContent = '⏹️ Stop Recording';
        this.recordBtn.classList.add('recording');
        
        try {
            this.recognition.start();
        } catch (error) {
            this.showError('Failed to start recording: ' + error.message);
            this.stopRecording();
        }
    }
    
    stopRecording() {
        this.isRecording = false;
        this.recordBtn.textContent = '🎙️ Start Recording';
        this.recordBtn.classList.remove('recording');
        
        if (this.recognition) {
            this.recognition.stop();
        }
    }
    
    copyToClipboard() {
        let textToCopy = this.transcriptionText.value;
        
        if (this.translationText.value.trim()) {
            textToCopy += '\\n\\nTranslation:\\n' + this.translationText.value;
        }
        
        navigator.clipboard.writeText(textToCopy).then(() => {
            this.updateStatus('Text copied to clipboard!', 'ready');
            setTimeout(() => {
                this.updateStatus('Ready', 'ready');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy text:', err);
        });
    }
    
    updateStatus(message, type) {
        this.status.textContent = message;
        this.status.className = \`status \${type}\`;
    }
    
    showError(message) {
        this.updateStatus(message, 'error');
        console.error(message);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AudioTranscriber();
});
`;

// package.json for Electron app
const package_json = `
{
  "name": "realtime-audio-transcriber",
  "version": "1.0.0",
  "description": "Real-time audio transcription and translation desktop app",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "dist": "electron-builder --publish=never"
  },
  "dependencies": {
    "electron": "^22.0.0"
  },
  "devDependencies": {
    "electron-builder": "^24.0.0"
  },
  "build": {
    "appId": "com.example.audio-transcriber",
    "productName": "Audio Transcriber",
    "directories": {
      "output": "dist"
    },
    "files": [
      "main.js",
      "index.html",
      "renderer.js"
    ],
    "win": {
      "target": "nsis"
    },
    "mac": {
      "target": "dmg"
    },
    "linux": {
      "target": "AppImage"
    }
  }
}
`;
`;

print("Implementation guide created successfully!")
print(f"Python code length: {len(python_code_example)} characters")
print(f"JavaScript code length: {len(javascript_code_example)} characters")

# Save the code examples to files for easy access
with open("python_implementation.py", "w") as f:
    f.write(python_code_example)

with open("javascript_implementation.js", "w") as f:
    f.write(javascript_code_example)

print("Code examples saved to files!")