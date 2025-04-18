import logging
from itertools import chain
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Optional, Type

from pydantic import AfterValidator, DirectoryPath, FilePath

from video_music_remover.common import (
    MusicRemoverData,
    extensions,
    resolve_path_factory,
    supported_file,
)
from video_music_remover.ffmpeg import VideoProcessor
from video_music_remover.music_remover_models import MusicRemover


class RemoveMusicFile:
    def __init__(
        self,
        original_video: Annotated[
            FilePath,
            AfterValidator(supported_file),
            AfterValidator(resolve_path_factory(strict=True)),
        ],
        output_directory: Annotated[
            DirectoryPath,
            AfterValidator(resolve_path_factory(strict=True)),
        ],
        base_directory: Annotated[
            Optional[DirectoryPath],
            AfterValidator(resolve_path_factory(strict=True)),
        ] = None,
    ):
        """:raise ValueError if base directory is not a relative path of original video or not an absolute path"""
        self.__original_video = original_video
        self.__no_music_video = output_directory.joinpath(
            original_video.relative_to(base_directory)
            if base_directory
            else original_video.name
        )
        self.__video_processor = VideoProcessor(original_video)

    @property
    def original_video(self) -> Path:
        return self.__original_video

    @property
    def no_music_video(self) -> Path:
        return self.__no_music_video

    @property
    def video_processor(self) -> VideoProcessor:
        return self.__video_processor


class RemoveMusicFromVideo:
    def __init__(
        self,
        file: RemoveMusicFile,
        music_remover_class: Type[MusicRemover],
    ):
        """:raise ValueError if base directory is not a relative path of original video or not an absolute path"""
        self.__original_video = file.original_video
        self.__no_music_video = file.no_music_video
        self.__video_processor = file.video_processor
        self.__music_remover_class = music_remover_class

    def process(self) -> None:
        logging.info(f'Processing file "{self.__original_video.name}"')
        print(f'Processing file "{self.__original_video.name}"')

        # TemporaryDirectory is cleaned up automatically
        with TemporaryDirectory(prefix="music-remover-") as temporary_directory:
            temporary_path = Path(temporary_directory)
            input_path = temporary_path.joinpath("input")
            intermediate_path = temporary_path.joinpath("intermediate")

            input_path.mkdir(parents=True, exist_ok=True)
            intermediate_path.mkdir(parents=True, exist_ok=True)

            input_audios = self.__video_processor.create_audio_streams(input_path)

            no_music_audios: list[Path] = []

            for index, audio in enumerate(input_audios):
                music_remover = self.__music_remover_class(audio, intermediate_path)

                counter = f"{index + 1}/{len(self.__video_processor.streams)}"

                logging.info(
                    f'"{self.__original_video.name}": start separating vocal... {counter}'
                )
                print(
                    f'"{self.__original_video.name}": start separating vocal... {counter}'
                )
                music_remover.remove_music()
                logging.info(
                    f'"{self.__original_video.name}": vocal seperated successfully {counter}'
                )
                print(
                    f'"{self.__original_video.name}": vocal seperated successfully {counter}'
                )
                no_music_audios.append(music_remover.no_music_sound)

            logging.info(
                f'"{self.__original_video.name}": creating a new video with no music...'
            )
            print(
                f'"{self.__original_video.name}": creating a new video with no music...'
            )
            self.__create_video_without_music(no_music_audios)
            logging.info(
                f'"{self.__original_video.name}": a new video with no music has been created'
            )
            print(
                f'"{self.__original_video.name}": a new video with no music has been created'
            )

            logging.info(f'"{self.__original_video.name}": deleting original video...')
            print(f'"{self.__original_video.name}": deleting original video...')
            self.__cleanup_original_video()
            logging.info(
                f'"{self.__original_video.name}": original video deleted successfully'
            )
            print(
                f'"{self.__original_video.name}": original video deleted successfully'
            )

        logging.info(f'"{self.__original_video.name}": Processing finished')
        print(f'"{self.__original_video.name}": Processing finished')

    def __create_video_without_music(self, no_music_paths: list[Path]) -> None:
        """
        replace the sound of the video with the no music version,
        and save the new video in the output folder
        regardless of the existence of the new video
        """
        # there's no check for the existence of new video with no music because it should be overwritten even if it exists
        # to ensure that no incomplete video is being created if the process failed in the middle of the process
        # assuming that original video is deleted by cleanup process when a video without music is created successfully

        # create missing directories in the path if exists
        self.__no_music_video.parent.mkdir(parents=True, exist_ok=True)
        self.__video_processor.replace_audio_streams(
            audios=no_music_paths, output_directory=self.__no_music_video.parent
        )

    def __cleanup_original_video(self) -> None:
        self.__original_video.unlink()


def get_original_video(input_path: Path) -> Path | None:
    logging.info(f'Looking for file to process in folder "{input_path.absolute()}"...')
    print(f'Looking for file to process in folder "{input_path.absolute()}"...')
    iterable = chain.from_iterable(input_path.rglob(f"*{ext}") for ext in extensions)

    return next(iterable, None)


def process_files(
    music_remover_data: MusicRemoverData, model: Type[MusicRemover]
) -> None:
    if music_remover_data.input_path.is_dir():
        logging.info("Mass processing started")
        print("Mass processing started")

        while original_video := get_original_video(music_remover_data.input_path):
            RemoveMusicFromVideo(
                file=RemoveMusicFile(
                    original_video=original_video,
                    output_directory=music_remover_data.output_path,
                    base_directory=music_remover_data.input_path,
                ),
                music_remover_class=model,
            ).process()
        else:
            logging.info("There's no file to process")
            print("There's no file to process")

        logging.info("Mass processing finished")
        print("Mass processing finished")
    else:
        # input is an existing file
        RemoveMusicFromVideo(
            file=RemoveMusicFile(
                original_video=music_remover_data.input_path,
                output_directory=music_remover_data.output_path,
            ),
            music_remover_class=model,
        ).process()
