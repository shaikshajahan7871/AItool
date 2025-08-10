# Create JavaScript/Electron implementation
javascript_implementation = '''
// JavaScript/Electron Implementation Files

// 1. package.json
{
  "name": "realtime-audio-transcriber",
  "version": "1.0.0",
  "description": "Real-time audio transcription and translation desktop app",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "dev": "electron . --debug"
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
      "renderer.js",
      "styles.css"
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

// 2. main.js (Electron Main Process)
const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1000,
        height: 700,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true
        },
        icon: path.join(__dirname, 'assets/icon.png'), // Add your app icon
        show: false // Don't show until ready
    });

    mainWindow.loadFile('index.html');
    
    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Handle window closed
    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Development tools
    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools();
    }
}

// App event handlers
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// Create application menu
const createMenu = () => {
    const template = [
        {
            label: 'File',
            submenu: [
                {
                    label: 'New Session',
                    accelerator: 'CmdOrCtrl+N',
                    click: () => {
                        mainWindow.webContents.send('clear-session');
                    }
                },
                {
                    label: 'Export Text',
                    accelerator: 'CmdOrCtrl+E',
                    click: () => {
                        mainWindow.webContents.send('export-text');
                    }
                },
                { type: 'separator' },
                {
                    label: 'Quit',
                    accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
                    click: () => {
                        app.quit();
                    }
                }
            ]
        },
        {
            label: 'Edit',
            submenu: [
                { role: 'copy' },
                { role: 'paste' },
                { role: 'selectall' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'forceReload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { type: 'separator' },
                { role: 'togglefullscreen' }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
};

app.whenReady().then(() => {
    createMenu();
});

// 3. index.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real-time Audio Transcription</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🎙️ Real-time Audio Transcription & Translation</h1>
            <div id="status" class="status ready">Ready to start recording</div>
        </header>
        
        <div class="controls">
            <button id="recordBtn" class="record-btn" title="Start/Stop Recording">
                <span class="btn-icon">🎙️</span>
                <span class="btn-text">Start Recording</span>
            </button>
            
            <div class="control-group">
                <label for="languageSelect">Target Language:</label>
                <select id="languageSelect" title="Select target language for translation">
                    <option value="auto">Auto-detect</option>
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
            </div>
            
            <button id="copyBtn" class="copy-btn" title="Copy transcription to clipboard">
                📋 Copy Text
            </button>
            
            <button id="clearBtn" class="clear-btn" title="Clear all text">
                🗑️ Clear
            </button>
        </div>
        
        <div class="content-area">
            <div class="transcription-section">
                <div class="section-header">
                    <label for="transcriptionText">Live Transcription</label>
                    <span class="word-count" id="transcriptionCount">0 words</span>
                </div>
                <textarea id="transcriptionText" 
                         readonly 
                         placeholder="Your speech will appear here in real-time..."
                         class="transcription-textarea"></textarea>
            </div>
            
            <div class="transcription-section">
                <div class="section-header">
                    <label for="translationText">Translation</label>
                    <span class="word-count" id="translationCount">0 words</span>
                </div>
                <textarea id="translationText" 
                         readonly 
                         placeholder="Translation will appear here..."
                         class="transcription-textarea"></textarea>
            </div>
        </div>
        
        <div class="footer">
            <div class="info">
                <span id="confidence" class="confidence">Confidence: --</span>
                <span id="language" class="language">Language: --</span>
                <span id="timing" class="timing">Duration: 00:00</span>
            </div>
        </div>
    </div>

    <!-- Loading overlay -->
    <div id="loadingOverlay" class="loading-overlay hidden">
        <div class="loading-content">
            <div class="spinner"></div>
            <p>Initializing speech recognition...</p>
        </div>
    </div>

    <script src="renderer.js"></script>
</body>
</html>

// 4. styles.css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    height: 100vh;
    overflow: hidden;
}

.container {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    margin: 10px;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    border: 1px solid rgba(255, 255, 255, 0.18);
}

header {
    padding: 20px 24px 16px;
    border-bottom: 1px solid #e9ecef;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 12px 12px 0 0;
}

header h1 {
    font-size: 24px;
    color: #2c3e50;
    margin-bottom: 8px;
    font-weight: 700;
}

.status {
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
}

.status.ready {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.status.recording {
    background: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
    animation: pulse 2s infinite;
}

.status.error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

.controls {
    padding: 16px 24px;
    display: flex;
    gap: 16px;
    align-items: center;
    flex-wrap: wrap;
    background: rgba(248, 249, 250, 0.8);
    border-bottom: 1px solid #e9ecef;
}

.record-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    background: linear-gradient(145deg, #28a745, #20c997);
    color: white;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.record-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(40, 167, 69, 0.4);
}

.record-btn.recording {
    background: linear-gradient(145deg, #dc3545, #e74c3c);
    box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
}

.control-group {
    display: flex;
    align-items: center;
    gap: 8px;
}

.control-group label {
    font-size: 14px;
    font-weight: 500;
    color: #495057;
}

select {
    padding: 8px 12px;
    border: 1px solid #ced4da;
    border-radius: 6px;
    font-size: 14px;
    background: white;
    cursor: pointer;
    transition: border-color 0.3s ease;
}

select:focus {
    outline: none;
    border-color: #80bdff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.copy-btn, .clear-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
}

.copy-btn {
    background: linear-gradient(145deg, #007bff, #0056b3);
    color: white;
    box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.copy-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}

.clear-btn {
    background: linear-gradient(145deg, #6c757d, #545b62);
    color: white;
    box-shadow: 0 2px 8px rgba(108, 117, 125, 0.3);
}

.clear-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(108, 117, 125, 0.4);
}

.content-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 24px;
    overflow: hidden;
}

.transcription-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.section-header label {
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
}

.word-count {
    font-size: 12px;
    color: #6c757d;
    background: #f8f9fa;
    padding: 4px 8px;
    border-radius: 4px;
}

.transcription-textarea {
    flex: 1;
    padding: 16px;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.5;
    resize: none;
    background: rgba(255, 255, 255, 0.9);
    transition: border-color 0.3s ease;
}

.transcription-textarea:focus {
    outline: none;
    border-color: #80bdff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.transcription-textarea::-webkit-scrollbar {
    width: 8px;
}

.transcription-textarea::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

.transcription-textarea::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
}

.transcription-textarea::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}

.footer {
    padding: 12px 24px;
    border-top: 1px solid #e9ecef;
    background: rgba(248, 249, 250, 0.8);
    border-radius: 0 0 12px 12px;
}

.info {
    display: flex;
    gap: 24px;
    font-size: 12px;
    color: #6c757d;
}

.confidence, .language, .timing {
    padding: 4px 8px;
    background: rgba(255, 255, 255, 0.8);
    border-radius: 4px;
    font-weight: 500;
}

.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(5px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.loading-content {
    text-align: center;
    color: white;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(255, 255, 255, 0.3);
    border-top: 4px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 16px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.hidden {
    display: none !important;
}

/* Responsive design */
@media (max-width: 768px) {
    .controls {
        flex-direction: column;
        gap: 12px;
        align-items: stretch;
    }
    
    .control-group {
        justify-content: center;
    }
    
    .content-area {
        padding: 16px;
    }
    
    .info {
        flex-direction: column;
        gap: 8px;
    }
}

// 5. renderer.js (Main Application Logic)
class AudioTranscriptionApp {
    constructor() {
        this.isRecording = false;
        this.recognition = null;
        this.targetLanguage = 'auto';
        this.startTime = null;
        this.timerInterval = null;
        this.wordCounts = { transcription: 0, translation: 0 };
        
        this.initializeElements();
        this.setupSpeechRecognition();
        this.bindEvents();
        this.updateTimer();
    }
    
    initializeElements() {
        // Main controls
        this.recordBtn = document.getElementById('recordBtn');
        this.copyBtn = document.getElementById('copyBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.languageSelect = document.getElementById('languageSelect');
        
        // Text areas
        this.transcriptionText = document.getElementById('transcriptionText');
        this.translationText = document.getElementById('translationText');
        
        // Status and info
        this.status = document.getElementById('status');
        this.confidence = document.getElementById('confidence');
        this.language = document.getElementById('language');
        this.timing = document.getElementById('timing');
        
        // Word counts
        this.transcriptionCount = document.getElementById('transcriptionCount');
        this.translationCount = document.getElementById('translationCount');
        
        // Loading overlay
        this.loadingOverlay = document.getElementById('loadingOverlay');
    }
    
    setupSpeechRecognition() {
        // Check for Web Speech API support
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.showError('Web Speech API not supported in this browser. Please use Chrome, Edge, or Safari.');
            this.recordBtn.disabled = true;
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        // Configure speech recognition
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;
        
        // Event handlers
        this.recognition.onstart = () => {
            this.updateStatus('🔴 Recording... Speak clearly into your microphone', 'recording');
            this.startTime = Date.now();
            this.startTimer();
        };
        
        this.recognition.onresult = (event) => {
            this.handleSpeechResult(event);
        };
        
        this.recognition.onerror = (event) => {
            this.handleSpeechError(event);
        };
        
        this.recognition.onend = () => {
            if (this.isRecording) {
                // Restart recognition if we're still supposed to be recording
                setTimeout(() => {
                    if (this.isRecording && this.recognition) {
                        try {
                            this.recognition.start();
                        } catch (e) {
                            console.warn('Recognition restart failed:', e);
                        }
                    }
                }, 100);
            } else {
                this.updateStatus('Recording stopped', 'ready');
                this.stopTimer();
            }
        };
    }
    
    async handleSpeechResult(event) {
        let interimTranscript = '';
        let finalTranscript = this.transcriptionText.value;
        let lastResult = null;
        
        // Process all results
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            const transcript = result[0].transcript;
            lastResult = result[0];
            
            if (result.isFinal) {
                finalTranscript += transcript + ' ';
                
                // Update confidence display
                if (result[0].confidence) {
                    this.updateConfidence(result[0].confidence);
                }
                
                // Translate if target language is different from auto
                if (this.targetLanguage !== 'auto' && transcript.trim()) {
                    await this.translateText(transcript.trim());
                }
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Update transcription display
        let displayText = finalTranscript;
        if (interimTranscript) {
            displayText += interimTranscript;
        }
        
        this.transcriptionText.value = displayText;
        this.updateWordCount('transcription', displayText);
        this.autoScroll(this.transcriptionText);
        
        // Update confidence if available
        if (lastResult && lastResult.confidence) {
            this.updateConfidence(lastResult.confidence);
        }
    }
    
    handleSpeechError(event) {
        let errorMessage = 'Speech recognition error';
        
        switch(event.error) {
            case 'no-speech':
                errorMessage = 'No speech detected. Please speak louder or check your microphone.';
                break;
            case 'audio-capture':
                errorMessage = 'Microphone access failed. Please check permissions.';
                break;
            case 'not-allowed':
                errorMessage = 'Microphone permission denied. Please allow access and refresh.';
                this.stopRecording();
                break;
            case 'network':
                errorMessage = 'Network error during speech recognition.';
                break;
            case 'aborted':
                // Usually happens when stopping recording, ignore
                return;
            default:
                errorMessage += `: ${event.error}`;
        }
        
        console.error('Speech recognition error:', event);
        this.showError(errorMessage);
        
        // Don't stop recording for temporary errors
        if (!['no-speech', 'audio-capture', 'network'].includes(event.error)) {
            this.stopRecording();
        }
    }
    
    async translateText(text) {
        if (!text.trim() || this.targetLanguage === 'auto') return;
        
        try {
            // Using Google Translate API (note: for production, use proper API keys)
            const response = await fetch(
                `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${this.targetLanguage}&dt=t&q=${encodeURIComponent(text)}`
            );
            
            if (!response.ok) throw new Error('Translation service unavailable');
            
            const data = await response.json();
            
            if (data && data[0] && data[0][0]) {
                const translatedText = data[0][0][0];
                const currentTranslation = this.translationText.value;
                const newTranslation = currentTranslation + translatedText + ' ';
                
                this.translationText.value = newTranslation;
                this.updateWordCount('translation', newTranslation);
                this.autoScroll(this.translationText);
                
                // Update detected language if available
                if (data[2]) {
                    this.updateDetectedLanguage(data[2]);
                }
            }
        } catch (error) {
            console.error('Translation error:', error);
            // Don't show translation errors to user unless critical
        }
    }
    
    bindEvents() {
        // Record button
        this.recordBtn.addEventListener('click', () => {
            this.toggleRecording();
        });
        
        // Copy button
        this.copyBtn.addEventListener('click', () => {
            this.copyToClipboard();
        });
        
        // Clear button
        this.clearBtn.addEventListener('click', () => {
            this.clearAllText();
        });
        
        // Language selection
        this.languageSelect.addEventListener('change', (e) => {
            this.targetLanguage = e.target.value;
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'r':
                        e.preventDefault();
                        this.toggleRecording();
                        break;
                    case 'c':
                        if (e.shiftKey) {
                            e.preventDefault();
                            this.copyToClipboard();
                        }
                        break;
                    case 'n':
                        e.preventDefault();
                        this.clearAllText();
                        break;
                }
            }
            
            // Space to toggle recording (when not in text field)
            if (e.code === 'Space' && !['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
                e.preventDefault();
                this.toggleRecording();
            }
        });
        
        // IPC events from main process
        if (typeof require !== 'undefined') {
            const { ipcRenderer } = require('electron');
            
            ipcRenderer.on('clear-session', () => {
                this.clearAllText();
            });
            
            ipcRenderer.on('export-text', () => {
                this.exportText();
            });
        }
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
        this.showLoading(true);
        
        try {
            this.isRecording = true;
            this.recordBtn.innerHTML = '<span class="btn-icon">⏹️</span><span class="btn-text">Stop Recording</span>';
            this.recordBtn.classList.add('recording');
            
            this.recognition.start();
            
            // Hide loading after a short delay
            setTimeout(() => this.showLoading(false), 1000);
            
        } catch (error) {
            this.showError('Failed to start recording: ' + error.message);
            this.stopRecording();
            this.showLoading(false);
        }
    }
    
    stopRecording() {
        this.isRecording = false;
        this.recordBtn.innerHTML = '<span class="btn-icon">🎙️</span><span class="btn-text">Start Recording</span>';
        this.recordBtn.classList.remove('recording');
        
        if (this.recognition) {
            this.recognition.stop();
        }
        
        this.stopTimer();
        this.showLoading(false);
    }
    
    copyToClipboard() {
        let textToCopy = this.transcriptionText.value.trim();
        
        if (this.translationText.value.trim()) {
            textToCopy += '\\n\\n--- TRANSLATION ---\\n' + this.translationText.value.trim();
        }
        
        if (!textToCopy) {
            this.updateStatus('No text to copy', 'error');
            return;
        }
        
        navigator.clipboard.writeText(textToCopy).then(() => {
            this.updateStatus('✅ Text copied to clipboard!', 'ready');
            setTimeout(() => {
                this.updateStatus('Ready to record', 'ready');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy text:', err);
            this.showError('Failed to copy text to clipboard');
        });
    }
    
    clearAllText() {
        this.transcriptionText.value = '';
        this.translationText.value = '';
        this.updateWordCount('transcription', '');
        this.updateWordCount('translation', '');
        this.updateStatus('Text cleared', 'ready');
        
        setTimeout(() => {
            this.updateStatus('Ready to record', 'ready');
        }, 1500);
    }
    
    exportText() {
        // This would typically save to a file
        // For now, just copy to clipboard
        this.copyToClipboard();
    }
    
    startTimer() {
        this.timerInterval = setInterval(() => {
            this.updateTimer();
        }, 1000);
    }
    
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }
    
    updateTimer() {
        if (!this.startTime) {
            this.timing.textContent = 'Duration: 00:00';
            return;
        }
        
        const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        
        this.timing.textContent = `Duration: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    
    updateWordCount(type, text) {
        const words = text.trim() ? text.trim().split(/\\s+/).length : 0;
        this.wordCounts[type] = words;
        
        if (type === 'transcription') {
            this.transcriptionCount.textContent = `${words} words`;
        } else if (type === 'translation') {
            this.translationCount.textContent = `${words} words`;
        }
    }
    
    updateConfidence(confidence) {
        const percentage = Math.round(confidence * 100);
        this.confidence.textContent = `Confidence: ${percentage}%`;
        
        // Color code based on confidence
        if (percentage >= 80) {
            this.confidence.style.color = '#28a745';
        } else if (percentage >= 60) {
            this.confidence.style.color = '#ffc107';
        } else {
            this.confidence.style.color = '#dc3545';
        }
    }
    
    updateDetectedLanguage(langCode) {
        this.language.textContent = `Language: ${langCode}`;
    }
    
    autoScroll(element) {
        element.scrollTop = element.scrollHeight;
    }
    
    updateStatus(message, type) {
        this.status.textContent = message;
        this.status.className = `status ${type}`;
    }
    
    showError(message) {
        this.updateStatus(message, 'error');
        console.error(message);
        
        // Auto-clear error after 5 seconds
        setTimeout(() => {
            if (this.status.classList.contains('error')) {
                this.updateStatus('Ready to record', 'ready');
            }
        }, 5000);
    }
    
    showLoading(show) {
        if (show) {
            this.loadingOverlay.classList.remove('hidden');
        } else {
            this.loadingOverlay.classList.add('hidden');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Real-time Audio Transcription App...');
    new AudioTranscriptionApp();
});

// Handle unload
window.addEventListener('beforeunload', (e) => {
    // Stop recording if active
    if (window.audioApp && window.audioApp.isRecording) {
        window.audioApp.stopRecording();
    }
});
'''

# Create individual files for the JavaScript implementation
files_to_create = {
    "package.json": '''
{
  "name": "realtime-audio-transcriber",
  "version": "1.0.0",
  "description": "Real-time audio transcription and translation desktop app",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "dev": "electron . --debug"
  },
  "dependencies": {
    "electron": "^22.0.0"
  },
  "devDependencies": {
    "electron-builder": "^24.0.0"
  }
}
''',
    
    "main.js": '''
const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1000,
        height: 700,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        show: false
    });

    mainWindow.loadFile('index.html');
    
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
''',

    "index.html": '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real-time Audio Transcription</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🎙️ Real-time Audio Transcription & Translation</h1>
            <div id="status" class="status ready">Ready to start recording</div>
        </header>
        
        <div class="controls">
            <button id="recordBtn" class="record-btn">
                <span class="btn-icon">🎙️</span>
                <span class="btn-text">Start Recording</span>
            </button>
            
            <div class="control-group">
                <label for="languageSelect">Target Language:</label>
                <select id="languageSelect">
                    <option value="auto">Auto-detect</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="it">Italian</option>
                    <option value="pt">Portuguese</option>
                    <option value="ru">Russian</option>
                    <option value="zh">Chinese</option>
                </select>
            </div>
            
            <button id="copyBtn" class="copy-btn">📋 Copy Text</button>
            <button id="clearBtn" class="clear-btn">🗑️ Clear</button>
        </div>
        
        <div class="content-area">
            <div class="transcription-section">
                <div class="section-header">
                    <label>Live Transcription</label>
                </div>
                <textarea id="transcriptionText" readonly class="transcription-textarea"
                         placeholder="Your speech will appear here in real-time..."></textarea>
            </div>
            
            <div class="transcription-section">
                <div class="section-header">
                    <label>Translation</label>
                </div>
                <textarea id="translationText" readonly class="transcription-textarea"
                         placeholder="Translation will appear here..."></textarea>
            </div>
        </div>
    </div>
    <script src="renderer.js"></script>
</body>
</html>
''',

    "styles.css": '''
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    height: 100vh;
    overflow: hidden;
}

.container {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: rgba(255, 255, 255, 0.95);
    margin: 10px;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
}

header {
    padding: 20px 24px 16px;
    border-bottom: 1px solid #e9ecef;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 12px 12px 0 0;
}

header h1 {
    font-size: 24px;
    color: #2c3e50;
    margin-bottom: 8px;
}

.status {
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
}

.status.ready {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.status.recording {
    background: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

.status.error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.controls {
    padding: 16px 24px;
    display: flex;
    gap: 16px;
    align-items: center;
    flex-wrap: wrap;
    background: rgba(248, 249, 250, 0.8);
    border-bottom: 1px solid #e9ecef;
}

.record-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    background: linear-gradient(145deg, #28a745, #20c997);
    color: white;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.record-btn.recording {
    background: linear-gradient(145deg, #dc3545, #e74c3c);
}

.control-group {
    display: flex;
    align-items: center;
    gap: 8px;
}

select, .copy-btn, .clear-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    cursor: pointer;
}

.copy-btn {
    background: #007bff;
    color: white;
}

.clear-btn {
    background: #6c757d;
    color: white;
}

.content-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 24px;
    overflow: hidden;
}

.transcription-section {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.transcription-textarea {
    flex: 1;
    padding: 16px;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    font-family: 'Consolas', monospace;
    font-size: 14px;
    resize: none;
    background: rgba(255, 255, 255, 0.9);
}
''',

    "renderer.js": '''
class AudioTranscriptionApp {
    constructor() {
        this.isRecording = false;
        this.recognition = null;
        this.targetLanguage = 'auto';
        
        this.initializeElements();
        this.setupSpeechRecognition();
        this.bindEvents();
    }
    
    initializeElements() {
        this.recordBtn = document.getElementById('recordBtn');
        this.copyBtn = document.getElementById('copyBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.languageSelect = document.getElementById('languageSelect');
        this.transcriptionText = document.getElementById('transcriptionText');
        this.translationText = document.getElementById('translationText');
        this.status = document.getElementById('status');
    }
    
    setupSpeechRecognition() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.showError('Web Speech API not supported in this browser');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        
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
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
                
                if (this.targetLanguage !== 'auto') {
                    await this.translateText(transcript);
                }
            } else {
                interimTranscript += transcript;
            }
        }
        
        this.transcriptionText.value = finalTranscript + interimTranscript;
        this.transcriptionText.scrollTop = this.transcriptionText.scrollHeight;
    }
    
    async translateText(text) {
        if (!text.trim()) return;
        
        try {
            const response = await fetch(
                `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${this.targetLanguage}&dt=t&q=${encodeURIComponent(text)}`
            );
            const data = await response.json();
            
            if (data && data[0] && data[0][0]) {
                const translatedText = data[0][0][0];
                this.translationText.value += translatedText + ' ';
                this.translationText.scrollTop = this.translationText.scrollHeight;
            }
        } catch (error) {
            console.error('Translation error:', error);
        }
    }
    
    bindEvents() {
        this.recordBtn.addEventListener('click', () => {
            this.toggleRecording();
        });
        
        this.copyBtn.addEventListener('click', () => {
            this.copyToClipboard();
        });
        
        this.clearBtn.addEventListener('click', () => {
            this.clearAllText();
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
        this.recordBtn.innerHTML = '<span class="btn-icon">⏹️</span><span class="btn-text">Stop Recording</span>';
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
        this.recordBtn.innerHTML = '<span class="btn-icon">🎙️</span><span class="btn-text">Start Recording</span>';
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
                this.updateStatus('Ready to record', 'ready');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy text:', err);
        });
    }
    
    clearAllText() {
        this.transcriptionText.value = '';
        this.translationText.value = '';
        this.updateStatus('Text cleared', 'ready');
    }
    
    updateStatus(message, type) {
        this.status.textContent = message;
        this.status.className = `status ${type}`;
    }
    
    showError(message) {
        this.updateStatus(message, 'error');
        console.error(message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new AudioTranscriptionApp();
});
'''
}

# Save all JavaScript files
for filename, content in files_to_create.items():
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ JavaScript/Electron implementation files created:")
for filename in files_to_create.keys():
    print(f"   • {filename}")

print(f"\n📊 Total files created: {len(files_to_create)} JavaScript files")
print("🚀 To run the Electron app:")
print("   1. npm install")
print("   2. npm start")