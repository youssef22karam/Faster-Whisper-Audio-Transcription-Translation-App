# Audio Transcription & Translation App

A real-time audio transcription and translation web application built with Flask and Whisper AI. Record audio directly in your browser and get instant transcriptions with multilingual translations.

## Features

- 🎤 **Real-time Audio Recording** - Record directly from your browser
- 🔊 **Audio Playback** - Listen to your recordings
- 📝 **AI Transcription** - Powered by OpenAI's Whisper model
- 🌍 **Multi-language Translation** - Translate to multiple languages simultaneously
- 📱 **Mobile-Friendly** - Responsive design optimized for mobile devices
- 🔒 **HTTPS Support** - Self-signed certificate for secure microphone access
- ⚡ **Fast Processing** - Optimized for quick transcription and translation

## Demo

The app provides a clean, mobile-optimized interface with:
- One-tap recording with audio feedback beeps
- Real-time transcription display
- Dual-language translation output
- Audio playback controls

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Required Dependencies

Install all required packages using pip:

```bash
pip install flask faster-whisper cryptography requests
```

### Individual Package Details

```bash
# Core web framework
pip install flask

# Fast Whisper implementation for transcription
pip install faster-whisper

# For SSL certificate generation
pip install cryptography

# For translation API calls
pip install requests
```

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/youssef22karam/Faster-Whisper-Audio-Transcription-Translation-App.git
   cd audio-transcription-app
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python Whisper ui.py
   ```

4. **Access the app:**
   - Open your browser and go to the HTTPS URL shown in the terminal
   - Accept the security warning (self-signed certificate)
   - Grant microphone permissions when prompted

## Configuration

### Language Settings

The app can be easily configured for different languages by modifying the settings at the top of `Whisper ui.py`:

```python
# Whisper transcription language (ISO 639-1 codes)
WHISPER_LANGUAGE = "es"  # Change to your desired language

# Translation settings
TRANSLATION_SOURCE_LANG = "es"  # Should match WHISPER_LANGUAGE
TRANSLATION_TARGET_1 = "en"     # First translation (English)
TRANSLATION_TARGET_2 = "ar"     # Second translation (Arabic)

# UI display names
TRANSLATION_TARGET_1_NAME = "English Translation"
TRANSLATION_TARGET_2_NAME = "Arabic Translation"
```

### Supported Languages

**Transcription (Whisper):** Supports 99+ languages including:
- English (`en`), Spanish (`es`), French (`fr`), German (`de`)
- Italian (`it`), Portuguese (`pt`), Russian (`ru`), Japanese (`ja`)
- Korean (`ko`), Chinese (`zh`), Arabic (`ar`), Hindi (`hi`)
- Dutch (`nl`), Swedish (`sv`), and many more

**Translation:** Supports all major world languages via Google Translate API

### Model Configuration

```python
MODEL_SIZE = "medium"    # Options: tiny, base, small, medium, large, large-v2, large-v3
DEVICE = "cpu"          # Options: cpu, cuda (if GPU available)
COMPUTE_TYPE = "int8"   # Options: int8, float16, float32
```

## File Structure

```
audio-transcription-app/
├── audio_transcription_app.py    # Main application file
├── uploads/                      # Temporary audio file storage
├── requirements.txt              # Python dependencies
└── README.md                    # This file
```

## API Endpoints

- `GET /` - Main application interface
- `POST /upload` - Upload audio file for transcription
- `POST /translate` - Translate text to configured languages

## Usage Tips

1. **First Run:** The app will download the Whisper model on first use (may take a few minutes)
2. **HTTPS Required:** Modern browsers require HTTPS for microphone access
3. **Mobile Optimization:** The interface is designed primarily for mobile use
4. **Network Translation:** Requires internet connection for translation features
5. **Audio Quality:** Clear audio recordings produce better transcription results

## Troubleshooting

### Common Issues

**Microphone not working:**
- Ensure you're accessing via HTTPS
- Grant microphone permissions in browser
- Check browser compatibility (Chrome/Firefox recommended)

**Model download fails:**
- Check internet connection
- Ensure sufficient disk space
- Try a smaller model size (`tiny` or `base`)

**Translation not working:**
- Verify internet connection
- Check if Google Translate is accessible in your region

### Performance Optimization

- Use `cpu` device for better compatibility
- Choose smaller models (`tiny`, `base`) for faster processing
- Use `int8` compute type for memory efficiency

## Hardware Requirements

- **Minimum:** 4GB RAM, 2GB free disk space
- **Recommended:** 8GB RAM, 4GB free disk space
- **GPU:** Optional (CUDA-compatible for faster processing)

## Browser Compatibility

- ✅ Chrome 60+
- ✅ Firefox 55+
- ✅ Safari 14+
- ✅ Edge 79+

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the transcription model
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) for the optimized implementation
- [Flask](https://flask.palletsprojects.com/) for the web framework

## Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Note:** This application uses a self-signed SSL certificate for local development. For production deployment, use a proper SSL certificate from a trusted Certificate Authority.
