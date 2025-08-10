
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
            textToCopy += '\n\nTranslation:\n' + this.translationText.value;
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
