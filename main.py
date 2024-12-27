import logging
import subprocess
import sys
from itertools import chain
from pathlib import Path
from typing import Type

from music_remover import DemucsMusicRemover, MusicRemover

logging.basicConfig(
    encoding='utf-8',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("removing_music.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)


class RemoveMusicFromVideo:
    def __init__(self, original_video: Path, music_remover_class: Type[MusicRemover], base_directory: Path = None):
        """:raise ValueError if base directory is not a relative path of original video or not an absolute path"""
        self.__original_video = original_video
        self.__music_remover = music_remover_class(original_video)
        self.__no_music_video = Path(
            f'output/{original_video.relative_to(base_directory) if base_directory else original_video.name}'
        )

    def process(self) -> None:
        try:
            if self.__music_remover.no_music_sound.exists():
                logging.info(f'"{self.__original_video.name}": vocal already separated, skipping separating vocal')
            else:
                logging.info(f'"{self.__original_video.name}": start separating vocal...')
                self.__music_remover.remove_music()
                logging.info(f'"{self.__original_video.name}": vocal seperated successfully')
        except subprocess.CalledProcessError as error:
            logging.error(
                f'"{self.__original_video.name}": an error prevented vocal separation process from being completed, refer to terminal for more info'
            )
            raise error

        logging.info(f'"{self.__original_video.name}": creating a new video with no music...')
        self.__create_video_without_music()
        logging.info(f'"{self.__original_video.name}": a new video with no music has been created')

        logging.info(f'"{self.__original_video.name}": deleting original video...')
        self.__cleanup_original_video()
        logging.info(f'"{self.__original_video.name}": original video deleted successfully')

        logging.info(f'"{self.__original_video.name}": deleting vocal sound...')
        self.__cleanup_intermediate_audio()
        logging.info(f'"{self.__original_video.name}": vocal sound deleted successfully')

    def __create_video_without_music(self) -> None:
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
                                                    '-i', self.__music_remover.no_music_sound.absolute(),
                                                    '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0',
                                                    self.__no_music_video.absolute()]
        subprocess.run(create_no_music_video_command, encoding='utf-8', check=True)

    def __cleanup_original_video(self) -> None:
        self.__original_video.unlink()

    def __cleanup_intermediate_audio(self) -> None:
        for file in [file for file in self.__music_remover.no_music_sound.parent.iterdir()]:
            file.unlink()
        self.__music_remover.no_music_sound.parent.rmdir()


def get_original_video(input_path: Path) -> Path | None:
    logging.info(f'Looking for file to process in folder "{input_path.absolute()}"...')
    extensions = ("mp4", "mkv", "webm")
    iterable = chain.from_iterable(input_path.rglob(f"*.{ext}") for ext in extensions)

    return next(iterable, None)


def main() -> None:
    input_path = Path('input')

    logging.info('Mass processing started')

    while original_video := get_original_video(input_path):
        logging.info(f'Processing file "{original_video.relative_to(input_path)}"')
        RemoveMusicFromVideo(original_video, DemucsMusicRemover, input_path).process()
        logging.info(f'"{original_video.relative_to(input_path)}": Processing finished')
    else:
        logging.info("There's no file to process")

    logging.info('Mass processing finished')


if __name__ == "__main__":
    # encapsulating the code of this block in a function ensures that scope of variables is not global
    sys.exit(main())
