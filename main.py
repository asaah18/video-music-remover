import errno
import logging
import subprocess
import sys
from itertools import chain
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Type

import typer

from custom_exceptions import UnsupportedFileError
from music_remover import MusicRemover, DemucsMusicRemover

app = typer.Typer()


class RemoveMusicFromVideo:
    def __init__(self, original_video: Path, music_remover_class: Type[MusicRemover], base_directory: Path = None):
        """:raise ValueError if base directory is not a relative path of original video or not an absolute path"""
        self.__original_video = original_video
        self.__music_remover_class = music_remover_class
        self.__no_music_video = Path(
            f'output/{original_video.relative_to(base_directory) if base_directory else original_video.name}'
        )

    def process(self) -> None:
        logging.info(f'Processing file "{self.__original_video.name}"')

        # TemporaryDirectory is cleaned up automatically
        with TemporaryDirectory(prefix='music-remover-') as temporary_directory:
            music_remover = self.__music_remover_class(self.__original_video, Path(temporary_directory))

            logging.info(f'"{self.__original_video.name}": start separating vocal...')
            music_remover.remove_music()
            logging.info(f'"{self.__original_video.name}": vocal seperated successfully')

            logging.info(f'"{self.__original_video.name}": creating a new video with no music...')
            self.__create_video_without_music(music_remover.no_music_sound)
            logging.info(f'"{self.__original_video.name}": a new video with no music has been created')

            logging.info(f'"{self.__original_video.name}": deleting original video...')
            self.__cleanup_original_video()
            logging.info(f'"{self.__original_video.name}": original video deleted successfully')

        logging.info(f'"{self.__original_video.name}": Processing finished')

    def __create_video_without_music(self, no_music_sound: Path) -> None:
        """
        replace the sound of the video with the no music version,
        and save the new video in folder 'output'
        regardless of the existence of the new video
        """
        # there's no check for the existence of new video with no music because it should be overwritten even if it exists
        # to ensure that no incomplete video is being created if the process failed in the middle of the process
        # assuming that original video is deleted by cleanup process when a video without music is created successfully

        # create missing directories in the path if exists
        self.__no_music_video.parent.mkdir(parents=True, exist_ok=True)

        # create video without music
        create_no_music_video_command: list[str] = ['ffmpeg', '-y', '-i', self.__original_video.absolute(),
                                                    '-i', no_music_sound.absolute(),
                                                    '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0',
                                                    self.__no_music_video.absolute()]
        subprocess.run(create_no_music_video_command, encoding='utf-8', check=True)

    def __cleanup_original_video(self) -> None:
        self.__original_video.unlink()


extensions = (".mp4", ".mkv", ".webm")


def is_supported_file(file: Path) -> bool:
    return file.suffix in extensions


def get_original_video(input_path: Path) -> Path | None:
    logging.info(f'Looking for file to process in folder "{input_path.absolute()}"...')
    iterable = chain.from_iterable(input_path.rglob(f"*{ext}") for ext in extensions)

    return next(iterable, None)


def validate_input_path(input_path: Path) -> None:
    """
    :raises FileNotFoundError
    :raises UnsupportedFileError
    """
    if not input_path.exists():
        raise FileNotFoundError(errno.ENOENT, 'No folder or file exists at the location specified',
                                input_path.resolve())

    if input_path.is_file() and not is_supported_file(input_path):
        raise UnsupportedFileError('this file is not a supported file type', input_path.resolve())


def process_files(input_path: Path) -> None:
    validate_input_path(input_path)

    if input_path.is_dir():
        logging.info('Mass processing started')

        while original_video := get_original_video(input_path):
            RemoveMusicFromVideo(original_video.resolve(), DemucsMusicRemover, input_path.resolve()).process()
        else:
            logging.info("There's no file to process")

        logging.info('Mass processing finished')
    else:
        # input is an existing file
        RemoveMusicFromVideo(input_path.resolve(), DemucsMusicRemover).process()


@app.command()
def main():
    logging.basicConfig(
        encoding='utf-8',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler("removing_music.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    process_files(Path('input'))


if __name__ == "__main__":
    app()
