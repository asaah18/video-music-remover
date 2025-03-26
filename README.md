# video-music-remover

a Python script to remove music from mp4 video files using [demux](https://github.com/facebookresearch/demucs) machine
learning model

## setup

- install [ffmpeg](https://ffmpeg.org) in your device
- install dependencies using [UV](https://docs.astral.sh/uv/)

## usage

- copy the videos you want to remove the music from to the folder "input"
- run the Python module `main.py` using the command `uv run video-music-remover`

the videos without music will be saved to the folder `output` and the original files in `input` folder will be
**deleted**.