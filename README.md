# video-music-remover

a Python script to remove music from mp4 and mkv video files using [demux](https://github.com/facebookresearch/demucs)
machine
learning model

## setup

- install [ffmpeg](https://ffmpeg.org) in your device
- install dependencies using [UV](https://docs.astral.sh/uv/)

## usage

1. run the Python module `main.py` using the command `uv run video-music-remover` and pass the input file/folder and
   output folder.
2. the program will process each supported file(mp4, mkv, webm) and produce a video without music in the corresponding
   output directory.