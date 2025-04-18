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
        completed_process = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-select_streams",
                "a",
                "-show_streams",
                "-print_format",
                "json",
                "-i",
                self._video,
            ],
            capture_output=True,
            text=True,
            check=True,
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

            command = [
                "ffmpeg",
                "-i",
                self._video,
                "-map",
                f"0:a:{index}",
                "-c",
                "copy",
                "-y",  # replace file if already exists
                file,
            ]
            subprocess.run(command, capture_output=True, text=True, check=True)
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

        output_file = output_directory.joinpath(self._video.name)

        # create video without music
        input_params: list[str] = ["-i", self._video]

        for audio in audios:
            input_params.extend(["-i", audio])

        options: list[str] = ["-y"]

        # copy all streams for mkv files, as it is compatible with the expected outputs of music remover models(mp3, wav and flac)
        if self._video.suffix == ".mkv":
            codec: list[str] = ["-c", "copy"]
        else:
            # copy all streams except audio streams
            codec: list[str] = [
                "-c:v",
                "copy",
                "-c:s",
                "copy",
                "-c:d",
                "copy",
                "-c:t",
                "copy",
            ]

        mapping: list[str] = ["-map", "0", "-map", "-0:a"]

        # add audio
        for index, _ in enumerate(audios):
            mapping.extend(["-map", f"{index + 1}:a:0"])

        metadata: list[str] = []

        # add corresponding metadata if exists
        for index, stream in enumerate(self.streams):
            if stream.tags.language:
                metadata.extend(
                    [f"-metadata:s:a:{index}", f"language={stream.tags.language}"]
                )

            if stream.tags.title:
                metadata.extend(
                    [f"-metadata:s:a:{index}", f"title={stream.tags.title}"]
                )

        command: list[str] = [
            "ffmpeg",
            *input_params,
            *options,
            *codec,
            *mapping,
            *metadata,
            output_file,
        ]

        subprocess.run(
            command,
            encoding="utf-8",
            capture_output=True,
            text=True,
            check=True,
        )
