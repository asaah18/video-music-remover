from itertools import chain
from logging import Logger
from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory
from typing import Annotated, Optional, Type

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    DirectoryPath,
    FilePath,
    model_validator,
    validate_call,
)
from typing_extensions import Self

from video_music_remover.common import (
    extensions,
    is_directories_conflicting,
    path_exists,
    resolve_path_factory,
    supported_file,
)
from video_music_remover.events import (
    LogObserver,
    MusicRemoveEventDispatcher,
    PrintObserver,
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
            DirectoryPath, AfterValidator(resolve_path_factory(strict=True))
        ],
        base_directory: Annotated[
            Optional[DirectoryPath], AfterValidator(resolve_path_factory(strict=True))
        ] = None,
    ):
        """:raise ValueError if base directory is not a relative path of original video or not an absolute path"""
        self.__original_video = original_video
        self.__no_music_video = output_directory.joinpath(
            original_video.relative_to(base_directory)
            if base_directory
            else original_video.name
        )

    @property
    def original_video(self) -> Path:
        return self.__original_video

    @property
    def no_music_video(self) -> Path:
        return self.__no_music_video


def remove_music_from_video(
    file: RemoveMusicFile,
    music_remover_class: Type[MusicRemover],
    event_dispatcher: MusicRemoveEventDispatcher,
) -> None:
    event_dispatcher.video_processing_started(original_video=file.original_video)
    video_processor = VideoProcessor(file.original_video)

    # TemporaryDirectory is cleaned up automatically
    with TemporaryDirectory(prefix="music-remover-") as temporary_directory:
        temporary_path = Path(temporary_directory)
        input_path = temporary_path.joinpath("input")
        intermediate_path = temporary_path.joinpath("intermediate")

        input_path.mkdir(parents=True, exist_ok=True)
        intermediate_path.mkdir(parents=True, exist_ok=True)

        input_audios = video_processor.create_audio_streams(input_path)

        no_music_audios: list[Path] = []

        for index, audio in enumerate(input_audios):
            music_remover = music_remover_class(audio, intermediate_path)

            counter = index + 1
            total = len(video_processor.streams)

            event_dispatcher.audio_processing_started(
                original_video=file.original_video, counter=counter, total=total
            )

            music_remover.remove_music()

            event_dispatcher.audio_processing_finished(
                original_video=file.original_video, counter=counter, total=total
            )

            no_music_audios.append(music_remover.no_music_sound)

        # create new video without music
        event_dispatcher.creating_new_video_started(
            original_video=file.original_video, new_video=file.no_music_video
        )
        file.no_music_video.parent.mkdir(parents=True, exist_ok=True)
        video_processor.replace_audio_streams(
            audios=no_music_audios, output_directory=file.no_music_video.parent
        )
        event_dispatcher.creating_new_video_finished(
            original_video=file.original_video, new_video=file.no_music_video
        )

    event_dispatcher.video_processing_finished(
        original_video=file.original_video, new_video=file.no_music_video
    )


class MusicRemoverData(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    input_path: Annotated[
        Path,
        AfterValidator(path_exists),
        AfterValidator(resolve_path_factory(strict=True)),
        AfterValidator(supported_file),
    ]
    output_path: Annotated[
        DirectoryPath, AfterValidator(resolve_path_factory(strict=True))
    ]

    @model_validator(mode="after")
    def __conflicting_directories(self) -> Self:
        if is_directories_conflicting(self.input_path, self.output_path):
            raise ValueError(
                "output path should not be a child or a parent or an exact of the input path"
            )
        return self

    def get_video(
        self, excluded_files: Optional[list[Path]] = None
    ) -> RemoveMusicFile | None:
        """
        get videos from input path

        :returns None if no video is found or input is file. Else, return a video file from input path
        """
        excluded_files = excluded_files if excluded_files else []

        iterable = chain.from_iterable(
            self.input_path.rglob(f"*{ext}") for ext in extensions
        )

        remove_music_file = None

        while remove_music_file is None:
            video = next(iterable, None)
            if video is None:
                break

            if video in excluded_files:
                continue

            remove_music_file = RemoveMusicFile(
                original_video=video,
                output_directory=self.output_path,
                base_directory=self.input_path,
            )
            if remove_music_file.no_music_video.exists():
                remove_music_file = None
                continue

        return remove_music_file


def process_files(
    music_remover_data: MusicRemoverData,
    model: Type[MusicRemover],
    logger: Optional[Logger] = None,
) -> None:
    excluded_files: list[Path] = []

    def get_video() -> RemoveMusicFile | None:
        if logger:
            logger.info(
                f'Looking for file to process in folder "{music_remover_data.input_path}"...'
            )
        print(
            f'Looking for file to process in folder "{music_remover_data.input_path}"...'
        )

        video = music_remover_data.get_video(excluded_files=excluded_files)

        if video is None:
            if logger:
                logger.info("There's no file to process")
            print("There's no file to process")

        return video

    event_dispatcher = MusicRemoveEventDispatcher(observers=[PrintObserver()])

    if logger:
        event_dispatcher.attach(LogObserver(logger))

    if music_remover_data.input_path.is_dir():
        if logger:
            logger.info("Mass processing started")
        print("Mass processing started")

        while original_video := get_video():
            try:
                remove_music_from_video(
                    file=original_video,
                    music_remover_class=model,
                    event_dispatcher=event_dispatcher,
                )
            except CalledProcessError as e:
                excluded_files.append(original_video.original_video)
                message = f"a cli error occurred while processing file {original_video.original_video}, skipping the file. error: {e}"
                print(message)
                if logger:
                    logger.error(message)

        if logger:
            logger.info("Mass processing finished")
        print("Mass processing finished")
    else:
        # input is an existing file
        remove_music_from_video(
            file=RemoveMusicFile(
                original_video=music_remover_data.input_path,
                output_directory=music_remover_data.output_path,
            ),
            music_remover_class=model,
            event_dispatcher=event_dispatcher,
        )
