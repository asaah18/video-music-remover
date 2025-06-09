# Video Music Remover

[![GitHub License](https://img.shields.io/github/license/asaah18/video-music-remover)](/LICENSE)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/video-music-remover)
[![PyPI - Version](https://img.shields.io/pypi/v/video-music-remover)](https://pypi.org/project/video-music-remover/)
[![Static Badge](https://img.shields.io/badge/package_manager-uv-blue?color=8A2BE2)](https://docs.astral.sh/uv/)

A powerful Python tool to remove background music from videos while preserving speech and other sounds using advanced
machine learning models.

## Overview

Video Music Remover is a command-line tool that uses the powerful [demucs](https://github.com/adefossez/demucs) machine
learning model to separate and remove music from videos while preserving speech, sound effects, and other audio
elements.
This is particularly useful for Muslim people and anyone who needs to remove music from videos.

The tool automatically processes all audio tracks in the input file, making it ideal for videos with multiple
language tracks or commentary audio tracks.

## Features

- **Batch Processing**: Process multiple videos in a directory with a single command
- **Multiple ML Models**: Choose from different machine learning models based on your needs
- **Preserves Video Quality**: Maintains the original video quality while only modifying the audio
- **Multiple Audio Tracks Support**: Automatically processes all audio tracks in the input video
- **Simple CLI Interface**: Easy-to-use command-line interface
- **Logging Support**: Optional logging for tracking processing progress
- **Original File Management**: Option to delete original files after processing

## Supported Formats

### Video Formats

- MP4 (.mp4)
- Matroska (.mkv)
- WebM (.webm)

### Machine Learning Models

- **demucs/htdemucs** (default): First version of Hybrid Transformer Demucs
- **demucs/htdemucs_ft**: Fine-tuned version of htdemucs (4x slower but potentially better quality)
- **demucs/mdx**: Trained only on MusDB HQ, winning model on track A at the MDX challenge
- **demucs/mdx_extra**: Trained with extra training data, ranked 2nd on track B of the MDX challenge

## System Requirements

- Python 3.10 or higher
- [FFmpeg](https://ffmpeg.org) (required for audio/video processing)
- Sufficient disk space for temporary files during processing

## Installation

### Using pip

```shell
pip install video-music-remover
```

### Using UV (recommended)

```shell
uv tool install video-music-remover
```

## Usage

### Basic Usage

To remove music from a single video:

```shell
video-music-remover remove-music input_video.mp4 output_directory/
```

To process all supported videos in a directory:

```shell
video-music-remover remove-music input_directory/ output_directory/
```

### Advanced Options

Specify a different machine learning model:

```shell
video-music-remover remove-music input_video.mp4 output_directory/ --model ht_demucs_ft
```

Enable logging to a file:

```shell
video-music-remover remove-music input_video.mp4 output_directory/ --log processing.log
```

Delete original files after successful processing:

```shell
video-music-remover remove-music input_video.mp4 output_directory/ --delete-original
```

### Health Check

Verify that all dependencies are correctly installed:

```shell
video-music-remover health-check
```

For detailed debugging information:

```shell
video-music-remover health-check --debug
```

### Version Information

Display the installed version:

```shell
video-music-remover version
```

## How It Works

The program processes videos through the following steps:

1. **Audio Extraction**: Extracts all audio tracks from the input video
   - if input is file, the new video file in the output directory will be replaced if exists
   - if input is a directory, only supported files that doesn't exist in the output directory will be processed
2. **Music Separation**: Uses the selected demucs model to separate vocals from music in all extracted audio tracks
3. **Audio Processing**: Preserves the vocal tracks and removes the music tracks
4. **Video Reconstruction**: Creates a new video with the original video track and the processed audio tracks while
   preserving other streams and metadata
5. **Original File Handling**: Optionally deletes original files when using `--delete-original`

The resulting video will have the same visual quality but with background music removed while preserving speech and
other sounds.

## Development Setup

### Package Manager

This project uses [UV](https://docs.astral.sh/uv/) as its package manager for development.

### Setting Up Development Environment

1. Clone the repository:
   ```shell
   git clone https://github.com/asaah18/video-music-remover.git
   cd video-music-remover
   ```

2. Create a virtual environment and install dependencies:
   ```shell
   uv venv
   uv sync
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
