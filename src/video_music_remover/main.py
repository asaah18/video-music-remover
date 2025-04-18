import logging
from itertools import chain
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Optional, Type

from pydantic import AfterValidator, DirectoryPath, FilePath, validate_call

from video_music_remover.common import (
    MusicRemoverData,
    extensions,
    resolve_path_factory,
    supported_file,
)
from video_music_remover.ffmpeg import VideoProcessor
from video_music_remover.music_remover_models import MusicRemover


class RemoveMusicFile:
    @validate_call
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


def remove_music_from_video(
    file: RemoveMusicFile, music_remover_class: Type[MusicRemover]
) -> None:
    logging.info(f'Processing file "{file.original_video.name}"')
    print(f'Processing file "{file.original_video.name}"')

    # TemporaryDirectory is cleaned up automatically
    with TemporaryDirectory(prefix="music-remover-") as temporary_directory:
        temporary_path = Path(temporary_directory)
        input_path = temporary_path.joinpath("input")
        intermediate_path = temporary_path.joinpath("intermediate")

        input_path.mkdir(parents=True, exist_ok=True)
        intermediate_path.mkdir(parents=True, exist_ok=True)

        input_audios = file.video_processor.create_audio_streams(input_path)

        no_music_audios: list[Path] = []

        for index, audio in enumerate(input_audios):
            music_remover = music_remover_class(audio, intermediate_path)

            counter = f"{index + 1}/{len(file.video_processor.streams)}"

            logging.info(
                f'"{file.original_video.name}": start separating vocal... {counter}'
            )
            print(f'"{file.original_video.name}": start separating vocal... {counter}')
            music_remover.remove_music()
            logging.info(
                f'"{file.original_video.name}": vocal seperated successfully {counter}'
            )
            print(
                f'"{file.original_video.name}": vocal seperated successfully {counter}'
            )
            no_music_audios.append(music_remover.no_music_sound)

        # create new video without music
        #   there's no check for the existence of new video with no music because it should be overwritten even if it exists
        #   to ensure that no incomplete video is being created if the process failed in the middle of the process
        #   assuming that original video is deleted by cleanup process when a video without music is created successfully

        logging.info(
            f'"{file.original_video.name}": creating a new video with no music...'
        )
        print(f'"{file.original_video.name}": creating a new video with no music...')

        file.no_music_video.parent.mkdir(parents=True, exist_ok=True)
        file.video_processor.replace_audio_streams(
            audios=no_music_audios,
            output_directory=file.no_music_video.parent,
        )

        logging.info(
            f'"{file.original_video.name}": a new video with no music has been created'
        )
        print(
            f'"{file.original_video.name}": a new video with no music has been created'
        )

        # cleanup original video
        logging.info(f'"{file.original_video.name}": deleting original video...')
        print(f'"{file.original_video.name}": deleting original video...')
        file.original_video.unlink()
        logging.info(
            f'"{file.original_video.name}": original video deleted successfully'
        )
        print(f'"{file.original_video.name}": original video deleted successfully')

    logging.info(f'"{file.original_video.name}": Processing finished')
    print(f'"{file.original_video.name}": Processing finished')


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
            remove_music_from_video(
                file=RemoveMusicFile(
                    original_video=original_video,
                    output_directory=music_remover_data.output_path,
                    base_directory=music_remover_data.input_path,
                ),
                music_remover_class=model,
            )
        else:
            logging.info("There's no file to process")
            print("There's no file to process")

        logging.info("Mass processing finished")
        print("Mass processing finished")
    else:
        # input is an existing file
        remove_music_from_video(
            file=RemoveMusicFile(
                original_video=music_remover_data.input_path,
                output_directory=music_remover_data.output_path,
            ),
            music_remover_class=model,
        )
