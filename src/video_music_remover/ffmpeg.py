import subprocess
from pathlib import Path
from typing import Annotated, List, Literal, Optional

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    DirectoryPath,
    FilePath,
    validate_call,
)

from video_music_remover.common import (
    resolve_path_factory,
    resolve_paths_factory,
    supported_file,
)
from video_music_remover.orms import FfmpegBuilder, FfprobeBuilder


class AudioStreamTag(BaseModel):
    model_config = ConfigDict(frozen=True)

    language: Optional[str] = None
    title: Optional[str] = None


class AudioStream(BaseModel):
    model_config = ConfigDict(frozen=True)

    index: int
    codec_name: str
    codec_type: Literal["audio"]
    start_pts: int
    start_time: float
    tags: AudioStreamTag


class MediaMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    streams: List[AudioStream]


class VideoProcessor:
    @validate_call
    def __init__(
        self,
        video: Annotated[
            FilePath,
            AfterValidator(supported_file),
            AfterValidator(resolve_path_factory(strict=True)),
        ],
    ) -> None:
        """
        :raises subprocess.CalledProcessError: if probe command fails
        """
        self._video = video
        self._metadata = self._probe_media_file()

    def _probe_media_file(self) -> MediaMetadata:
        """
        :raises subprocess.CalledProcessError: if probe command fails
        """
        ffprobe_builder = FfprobeBuilder()
        ffprobe_builder.log_level("quiet")
        ffprobe_builder.select_stream("a")
        ffprobe_builder.show_streams()
        ffprobe_builder.print_format("json")
        ffprobe_builder.input(self._video)

        completed_process = subprocess.run(
            ffprobe_builder.command, capture_output=True, text=True, check=True
        )
        return MediaMetadata.model_validate_json(completed_process.stdout)

    @property
    def streams(self) -> list[AudioStream]:
        return self._metadata.streams

    @validate_call
    def create_audio_streams(
        self,
        directory: Annotated[
            DirectoryPath, AfterValidator(resolve_path_factory(strict=True))
        ],
    ) -> list[Path]:
        """
        replace audio streams with new audio, audio files are replaced with their respected audio stream

        replace existing file if exists
        """
        files: list[Path] = []

        for index, stream in enumerate(self.streams):
            file: Path = directory.joinpath(f"input_{index}{self._video.suffix}")

            builder = FfmpegBuilder()
            builder.input(self._video)
            builder.stream_index_map(
                negative_mapping=False, input_index=0, stream="a", stream_index=index
            )
            builder.codec(codec="copy")
            builder.replace_if_exists()
            builder.output(file)

            subprocess.run(builder.command, capture_output=True, text=True, check=True)
            files.append(file)

        return files

    @validate_call
    def replace_audio_streams(
        self,
        audios: Annotated[
            list[FilePath], AfterValidator(resolve_paths_factory(strict=True))
        ],
        output_directory: Annotated[
            DirectoryPath, AfterValidator(resolve_path_factory(strict=True))
        ],
    ) -> None:
        """
        replace the sounds of the video with the no music version while keeping the metadata
        assuming that they are passed in the same order as the original audio streams
        and save the new video in the output folder

        - there's no check for the existence of new video with no music because it should be overwritten even if it exists
         to ensure that no incomplete video is being created if the process failed in the middle of the process
         assuming that original video is deleted by cleanup process when a video without music is created successfully

        :raises ValueError: if the number of new audio files exceeds the number of audio streams of the video
        """
        if len(self.streams) < len(audios):
            raise ValueError(
                "number of new audio files should not exceed the number of audio streams of the video"
            )

        temporary_output_file = output_directory.joinpath(
            f".music_remover_output{self._video.suffix}"
        )
        output_file = output_directory.joinpath(self._video.name)

        # create video without music
        builder = FfmpegBuilder()

        builder.input(self._video)

        for audio in audios:
            builder.input(audio)

        builder.replace_if_exists()

        # copy all streams for mkv files, as it is compatible with the expected outputs of music remover models(mp3, wav and flac)
        if self._video.suffix == ".mkv":
            builder.codec(codec="copy")
        else:
            # copy all streams except audio streams
            builder.codec(codec="copy", stream="v")
            builder.codec(codec="copy", stream="s")
            builder.codec(codec="copy", stream="d")
            builder.codec(codec="copy", stream="t")

        builder.map(negative_mapping=False, input_index=0)
        builder.map(negative_mapping=True, input_index=0, stream="a")

        # add audio
        for index, _ in enumerate(audios):
            builder.stream_index_map(
                negative_mapping=False,
                input_index=index + 1,
                stream="a",
                stream_index=0,
            )

        # add corresponding metadata if exists
        for index, stream in enumerate(self.streams):
            if stream.tags.language:
                builder.audio_metadata(
                    index=index, key="language", value=stream.tags.language
                )

            if stream.tags.title:
                builder.audio_metadata(
                    index=index, key="title", value=stream.tags.title
                )

        builder.output(temporary_output_file)

        subprocess.run(
            builder.command,
            encoding="utf-8",
            capture_output=True,
            text=True,
            check=True,
        )

        temporary_output_file.replace(output_file)
