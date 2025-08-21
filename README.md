# ✨ Noise Cancellation Studio

A modern, production-ready desktop application for removing background noise from audio and video files using advanced signal processing and machine learning techniques. Features a sleek dark theme with glassmorphism effects and professional-grade audio processing capabilities.

![Application Screenshot](docs/screenshot.png)

## Features

### 🎯 **Multiple Noise Reduction Engines**
- **Spectral Gating**: Traditional frequency-domain noise reduction with customizable parameters
- **RNNoise**: State-of-the-art neural network-based noise reduction optimized for speech
- **Demucs** (Optional): Advanced source separation using deep learning

### 🔧 **Professional Audio Processing**
- Batch processing with parallel execution
- Real-time preview with waveform visualization
- EBU R128 loudness normalization
- Video remuxing to preserve video streams and metadata
- Support for all major audio and video formats

### 🎨 **Modern User Interface**
- **Sleek Dark Theme**: Professional dark interface with glassmorphism effects
- **Modern Design**: Compact, well-aligned components with gradient animations
- **Interactive Elements**: Responsive buttons with hover effects and smooth transitions  
- **Visual Feedback**: Animated progress indicators and status displays
- **Enhanced Controls**: Improved spinbox arrows, modern input fields, and styled components
- **Drag-and-Drop**: Intuitive file handling with visual feedback
- **Real-time Preview**: Waveform visualization with before/after comparison
- **Comprehensive Logging**: Expandable log viewer with syntax highlighting

### 📈 **Advanced Features**
- Automatic noise profile detection
- Manual noise region selection for spectral gating
- Configurable output patterns and formats
- Detailed processing logs and error handling
- System requirements validation

## Installation

### Prerequisites

- **Python 3.10+**
- **FFmpeg** (required for media processing)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd noise-cancellation
   ```

2. **Set up the environment:**
   ```bash
   make setup
   ```

3. **Download RNNoise models:**
   ```bash
   make download-models
   ```

4. **Run the application:**
   ```bash
   make run
   # or directly:
   python app.py
   ```

   The application will launch with a modern dark interface optimized for professional audio work.

### Platform-Specific Installation

#### Windows
1. Install Python 3.10+ from [python.org](https://python.org)
2. Download FFmpeg from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add to PATH
3. Run the setup commands above in Command Prompt or PowerShell

#### macOS
1. Install Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
2. Install dependencies: `brew install python@3.10 ffmpeg`
3. Run the setup commands above

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip ffmpeg
```
Then run the setup commands above.

## Usage Guide

### Modern Interface Overview

The application features a **modern 3-panel layout**:
- **Left Panel**: File queue with drag-and-drop support and batch controls
- **Right Panel**: Tabbed interface with Settings and Preview panels
- **Bottom Panel**: Expanded processing logs with real-time updates

### Basic Workflow

1. **Add Files**: 
   - Drag and drop audio/video files directly onto the interface
   - Use the **⊕ Add** button in the header for quick file selection
   - Or use File → Add Files menu option

2. **Configure Settings**: 
   - Switch to the **⚙️ Settings** tab in the right panel
   - Choose your noise reduction engine from the dropdown
   - Adjust parameters using the enhanced number input fields with visible arrows

3. **Preview Processing**: 
   - Select a file from the queue 
   - Switch to the **👁️ Preview** tab
   - Set start time and duration using the improved spinbox controls
   - Click **▶ Preview** to test settings with waveform comparison

4. **Batch Processing**: 
   - Configure parallel jobs in the **⚙️ Settings** section of the left panel
   - Enable "Continue on error" and "Auto-clear completed" as needed
   - Click **▶ Process** in the header or **▶ Start** in the batch controls
   - Monitor progress with real-time statistics and ETA

5. **Review Results**: 
   - Check detailed processing statistics in the expanded stats section
   - Monitor logs in the bottom panel with improved readability
   - Review success/failure rates and timing information

### Noise Reduction Engines

#### Spectral Gating
Best for: Stationary background noise (fans, hum, static)

**Key Settings:**
- **Noise Reduction**: Amount of noise to reduce (5-60 dB)
- **Noise Type**: Stationary vs. non-stationary
- **Smoothing**: Temporal and frequency smoothing to reduce artifacts
- **Noise Profile**: Automatic detection or manual time range selection

#### RNNoise
Best for: Speech with various noise types (ideal for podcasts, interviews)

**Key Settings:**
- **Model**: Choose from pre-trained models (broadband, speech-heavy, music, cassette)
- **Mix Factor**: Blend between original and processed audio
- **Sample Rate**: Processing sample rate (48kHz recommended)

#### Demucs (Advanced)
Best for: Complex audio with multiple sources (music, live recordings)

**Key Settings:**
- **Model**: htdemucs (highest quality), hdemucs_mmi (balanced), mdx_extra (fastest)
- **Device**: CPU, CUDA (NVIDIA GPU), or MPS (Apple Silicon)
- **Reduction Strength**: How aggressively to reduce background elements
- **Processing Settings**: Segment length, overlap, parallel jobs

### File Formats

**Supported Input Formats:**
- Audio: WAV, MP3, FLAC, AAC, OGG, M4A, WMA, AIFF
- Video: MP4, AVI, MKV, MOV, WMV, FLV, WebM, M4V

**Output Formats:**
- **Lossless**: WAV, FLAC
- **Compressed**: MP3, AAC
- **Video**: Original format with replaced audio track

### Advanced Features

#### Custom Output Patterns
Configure output file naming in Preferences → Paths:
- `{parent}/clean/{name}_clean{ext}` (default)
- `{parent}/processed/{name}_processed{ext}`
- `/custom/output/dir/{name}{ext}`

#### Advanced Batch Processing
- **Enhanced Controls**: Modern interface with ▶ Start, ⏸ Pause, ⏹ Stop buttons
- **Parallel Processing**: Configurable job count with improved number input controls
- **Smart Options**: Continue on error and auto-clear completed files
- **Detailed Statistics**: Expanded stats panel showing:
  - ⚡ Real-time processing status with file counts  
  - ✅ Success vs ❌ failure tracking with percentages
  - 🕰️ Elapsed time and ETA calculations
  - 📈 Average processing time per file
  - 🎯 Completion rates and remaining file counts
- **Visual Progress**: Animated progress bars with percentage completion

#### Enhanced Preview System
- **Time Range Selection**: Choose any 5-30 second segment with improved spinbox controls
- **Waveform Visualization**: Side-by-side comparison of 🔵 original vs 🟢 processed audio
- **Audio Playback**: Play original and cleaned versions using 🔊 buttons  
- **Real-time Analysis**: Detailed RMS and peak level analysis in expanded text area
- **Visual Feedback**: Modern progress indicators during preview processing

## Troubleshooting

### Common Issues

#### FFmpeg Not Found
**Error**: "FFmpeg not found in system PATH"

**Solutions:**
1. Install FFmpeg and add to system PATH
2. Set custom FFmpeg path in Preferences → Paths → FFmpeg Path
3. Test installation with the "Test" button

#### RNNoise Models Missing
**Error**: "No RNNoise models found"

**Solutions:**
1. Run `make download-models`
2. Manually download models from [xiph/rnnoise-models](https://github.com/xiph/rnnoise-models)
3. Place `.rnnn` files in the `models/` directory

#### Processing Errors
**Common causes:**
- Insufficient disk space
- Corrupted input files
- Unsupported codec/format
- Memory limitations

**Solutions:**
1. Check available disk space
2. Try different input files
3. Reduce parallel job count
4. Check log panel for detailed error messages

#### Performance Issues
**For large files or slow processing:**
1. Reduce parallel job count
2. Use faster engines (Spectral Gate > RNNoise > Demucs)
3. Process shorter segments
4. Use GPU acceleration for Demucs (if available)

### Getting Help

1. **Check Logs**: View detailed information in the Logs panel
2. **Open Logs Folder**: Use the button to access log files for debugging
3. **Validate System**: File → Preferences validates your setup
4. **Reset Settings**: Use "Reset All Settings" if configuration is corrupted

## Performance Tips

### For Best Quality
- Use RNNoise for speech content
- Use Demucs for complex music/multi-source audio
- Enable loudness normalization for consistent output levels
- Preview different settings before batch processing

### For Best Speed
- Use Spectral Gating for simple noise reduction
- Increase parallel jobs (up to CPU core count)
- Use SSD storage for faster I/O
- Process shorter audio segments when possible

### Memory Optimization
- Reduce parallel job count if running out of memory
- Use lower sample rates for processing (if quality allows)
- Close other applications during large batch jobs

## Technical Architecture

### Core Components
- **Processing Pipeline**: Manages job queues and execution with thread safety
- **Media Handling**: FFmpeg integration for comprehensive format support
- **Noise Reduction Engines**: Pluggable architecture for different algorithms
- **Modern UI Framework**: PySide6 (Qt) with custom styling and animations
- **Theme System**: Dark glassmorphism theme with gradient effects
- **Animation Engine**: Smooth transitions and visual feedback throughout the interface

### Dependencies
- **Core**: Python 3.10+, PySide6, NumPy, SciPy
- **Audio Processing**: librosa, soundfile, noisereduce, pyloudnorm  
- **Media I/O**: ffmpeg-python (with FFmpeg binary)
- **UI Enhancements**: Custom Qt stylesheets with glassmorphism effects
- **Optional**: demucs (for advanced source separation)

### Project Structure
```
noise-cancellation/
├── app.py              # Main application entry point
├── ui/                 # User interface components
│   ├── main_window.py  # Modern main interface with animations
│   ├── modern_styles.py # Dark theme with glassmorphism effects
│   ├── animated_widgets.py # Custom animated UI components
│   ├── icon_provider.py # Modern SVG icon system
│   └── gradient_background.py # Animated backgrounds and effects
├── core/               # Core processing logic
├── engines/            # Noise reduction engines
├── utils/              # Utility functions
├── tests/              # Unit tests
├── models/             # RNNoise model files
├── logs/               # Application logs
└── config/             # Configuration files
```

## Development

### Running Tests
```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
make test
# or
python -m pytest tests/ -v
```

### Code Quality
```bash
# Format code
make lint

# Type checking
make type-check
```

### Building Distribution
```bash
# Create distribution packages
python -m build

# Install locally
pip install -e .
```

## License

This project is released under the MIT License. See `LICENSE` file for details.

## Acknowledgments

- **RNNoise**: Xiph.org Foundation for the RNNoise neural network
- **Demucs**: Facebook Research for the Demucs source separation model
- **FFmpeg**: The FFmpeg team for multimedia processing
- **librosa**: librosa development team for audio analysis tools

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any improvements.

### Development Setup
1. Fork the repository
2. Create a virtual environment: `python -m venv venv`
3. Install in development mode: `pip install -e .[dev]`
4. Make your changes and add tests
5. Run tests: `make test`
6. Submit a pull request

## Changelog

### v2.0.0 (Modern UI Update)
- **🎨 Complete UI Redesign**: Modern dark theme with glassmorphism effects
- **✨ Enhanced Animations**: Smooth transitions, hover effects, and visual feedback
- **🎯 Improved Layout**: Compact, well-aligned 3-panel interface (950×700 window)
- **📊 Enhanced Statistics**: Expanded batch processing stats with real-time updates
- **🔧 Better Controls**: Improved spinbox arrows and number input fields
- **📝 Enhanced Logging**: Larger, more readable log area with syntax highlighting
- **🎪 Visual Polish**: Gradient backgrounds, modern icons, and professional styling
- **⚡ Performance**: Optimized rendering and responsive interface elements

### v1.0.0 (Initial Release)
- Complete noise reduction pipeline with multiple engines
- Professional GUI with batch processing
- Support for audio and video file processing
- Real-time preview and waveform visualization
- Comprehensive configuration and logging system
- Cross-platform compatibility (Windows, macOS, Linux)

## Interface Preview

The new modern interface features:
- **Header Bar**: Quick access to ⊕ Add Files and ▶ Process buttons
- **Left Panel**: File queue with enhanced batch processing controls
- **Right Panel**: Tabbed ⚙️ Settings and 👁️ Preview panels  
- **Bottom Panel**: Expanded 📋 Processing Logs with improved readability
- **Dark Theme**: Professional glassmorphism design with purple/blue accents
- **Animations**: Smooth fade-ins, hover effects, and progress animations

---

For more information, bug reports, or feature requests, please visit our [GitHub repository](https://github.com/your-username/noise-cancellation).

**✨ Noise Cancellation Studio v2.0** - Professional audio processing with modern design.