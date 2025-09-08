from pathlib import Path
from typing import List, Literal, Type

import demucs.separate

DemucsModels: Type[str] = Literal[
    "htdemucs", "htdemucs_ft", "mdx", "mdx_extra", "mdx_extra_q"
]


class DemucsBuilder:
    def __init__(self, file: Path) -> None:
        self.__arguments: List[str] = [str(file)]

    def separate(self) -> None:
        demucs.separate.main(self.__arguments)

    def two_stems(self, stem: Literal["vocals"]) -> None:
        """Only separate audio into {STEM} and no_{STEM}."""
        self.__arguments.extend(["--two-stems", stem])

    def model(self, model: DemucsModels) -> None:
        """Pretrained model name or signature. Default is htdemucs"""
        self.__arguments.extend(["-n", model])

    def wav_output(self, size: Literal["int24", "float32"]) -> None:
        """Save wav output as either int24 or float32(2x bigger) wav"""
        self.__arguments.append(f"--{size}")

    def save_as(self, extension: Literal["mp3", "flac"]) -> None:
        """Convert the output wavs to mp3 or flac"""
        self.__arguments.append(f"--{extension}")

    def output_directory(self, directory: Path) -> None:
        """
        Folder where to put extracted tracks.

        A subfolder with the model name will be created.
        """
        self.__arguments.extend(["-o", str(directory)])
