from pathlib import Path
from typing import List, Literal, Optional, Type

from typing_extensions import Self

Stream: Type[str] = Literal["v", "a", "s", "d", "t"]
DemucsModels: Type[str] = Literal[
    "htdemucs", "htdemucs_ft", "mdx", "mdx_extra", "mdx_extra_q"
]


class FfmpegBuilder:
    def __init__(self) -> None:
        self.__command: List[str] = ["ffmpeg"]

    @property
    def command(self) -> List[str]:
        return self.__command.copy()

    def version(self) -> None:
        self.__command.append("-version")

    def input(self, input_file: Path) -> None:
        self.__command.extend(["-i", input_file])

    def map(
        self, negative_mapping: bool, input_index: int, stream: Optional[Stream] = None
    ) -> None:
        mapping: str = "-" if negative_mapping else ""
        mapping += str(input_index) if stream is None else f"{input_index}:{stream}"

        self.__command.extend(["-map", mapping])

    def stream_index_map(
        self,
        negative_mapping: bool,
        input_index: int,
        stream: Stream,
        stream_index: int,
    ) -> None:
        mapping: str = "-" if negative_mapping else ""
        mapping += f"{input_index}:{stream}:{stream_index}"

        self.__command.extend(["-map", mapping])

    def codec(
        self, codec: str | Literal["copy"], stream: Optional[Stream] = None
    ) -> None:
        self.__command.extend(["-c" if stream is None else f"-c:{stream}", codec])

    def audio_metadata(
        self, index: int, key: Literal["title", "language"], value: str
    ) -> None:
        self.__command.extend([f"-metadata:s:a:{index}", f"{key}={value}"])

    def replace_if_exists(self) -> None:
        self.__command.append("-y")

    def output(self, output_file: Path) -> None:
        self.__command.append(str(output_file))

    @classmethod
    def health_check(cls) -> Self:
        instance = cls()
        instance.version()
        return instance


class FfprobeBuilder:
    def __init__(self) -> None:
        self.__command: List[str] = ["ffprobe"]

    @property
    def command(self) -> List[str]:
        return self.__command.copy()

    def version(self) -> None:
        self.__command.append("-version")

    def log_level(
        self,
        level: Literal[
            "quiet",
            "panic",
            "fatal",
            "error",
            "warning",
            "info",
            "verbose",
            "debug",
            "trace",
        ],
    ) -> None:
        self.__command.extend(["-v", level])

    def select_stream(self, stream: Stream) -> None:
        self.__command.extend(["-select_streams", stream])

    def show_streams(self) -> None:
        self.__command.append("-show_streams")

    def print_format(
        self,
        print_format: Literal[
            "default", "compact", "csv", "flat", "ini", "json", "xml"
        ],
    ) -> None:
        self.__command.extend(["-print_format", print_format])

    def input(self, file_input: Path) -> None:
        self.__command.extend(["-i", file_input])

    @classmethod
    def health_check(cls) -> Self:
        instance = cls()
        instance.version()
        return instance


class DemucsBuilder:
    def __init__(self, file: Optional[Path] = None) -> None:
        self.__command: List[str] = ["demucs"]
        self.__file = file

    @property
    def command(self) -> List[str]:
        command = self.__command.copy()
        if self.__file:
            command.append(str(self.__file))

        return command

    def help(self) -> None:
        self.__command.append("-h")

    @classmethod
    def health_check(cls) -> Self:
        instance = cls()
        instance.help()
        return instance

    def two_stems(self, stem: Literal["vocals"]) -> None:
        """Only separate audio into {STEM} and no_{STEM}."""
        self.__command.extend(["--two-stems", stem])

    def model(self, model: DemucsModels) -> None:
        """Pretrained model name or signature. Default is htdemucs"""
        self.__command.extend(["-n", model])

    def wav_output(self, size: Literal["int24", "float32"]) -> None:
        """Save wav output as either int24 or float32(2x bigger) wav"""
        self.__command.append(f"--{size}")

    def save_as(self, extension: Literal["mp3", "flac"]) -> None:
        """Convert the output wavs to mp3 or flac"""
        self.__command.append(f"--{extension}")

    def output_directory(self, directory: Path) -> None:
        """
        Folder where to put extracted tracks.

        A subfolder with the model name will be created.
        """
        self.__command.extend(["-o", directory])
