# video-music-remover

a Python script to remove music from supported video files using [demucs](https://github.com/adefossez/demucs)
machine learning model.

The supported machine learning models are:

- demucs/htdemucs
- demucs/mdx_extra_q

The supported video files are:

- mp4
- mkv
- webm

## setup

### requirements

- install [ffmpeg](https://ffmpeg.org)

### package manager

this project is using [UV](https://docs.astral.sh/uv/) package manager

## usage

Run the command "video-music-remover" followed by input file/folder and output folder. There are other options in the
command for choosing the AI model to use for separating audio steams and other options.

The program will process each supported file from input and produce a video without music in the
corresponding output folder.