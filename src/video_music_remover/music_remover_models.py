import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Optional, Type

from pydantic import DirectoryPath, FilePath, validate_call


class MusicRemover(ABC):
    @validate_call
    def __init__(
        self, original_video: FilePath, output_directory: Optional[DirectoryPath] = None
    ):
        self._original_video: Path = original_video
        self._output_directory: Path = (
            output_directory
            if output_directory
            else self._get_default_output_directory()
        )
        self.__no_music_sound: Path = self._get_no_music_audio_path(original_video)

    @property
    def no_music_sound(self) -> Path:
        return self.__no_music_sound

    @abstractmethod
    def _get_no_music_audio_path(self, video_path: Path) -> Path:
        pass

    @abstractmethod
    def _get_default_output_directory(self) -> Path:
        """the default output directory to be used if no output directory is provided"""
        pass

    @abstractmethod
    def remove_music(self) -> None:
        """
        separate vocal from music using machine learning model

        :exception subprocess.CalledProcessError
        """
        pass


class DemucsMusicRemover(MusicRemover, ABC):
    @abstractmethod
    def _get_model(self) -> str:
        """
        the models to choose from are: htdemucs, mdx_extra_q
        """
        pass

    def _get_default_output_directory(self) -> Path:
        return Path("separated")

    def _get_no_music_audio_path(self, video_path: Path) -> Path:
        return self._output_directory.joinpath(
            f"{self._get_model()}/{video_path.stem}/vocals.mp3"
        )

    def remove_music(self) -> None:
        options: list[str] = [
            "--mp3",
            "--two-stems=vocals",
            "-n",
            self._get_model(),
            "-o",
            self._output_directory.absolute(),
        ]
        remove_music_command: list[str] = ["demucs", *options, self._original_video]

        subprocess.run(remove_music_command, encoding="utf-8", check=True)
        # raise exception if vocal sound is not created
        # exception raised manually because demucs command doesn't return error code
        if not self.no_music_sound.exists():
            raise subprocess.CalledProcessError(returncode=1, cmd=remove_music_command)


class HTDemucsMusicRemover(DemucsMusicRemover):
    """
    the latest Hybrid Transformer Demucs model.
    In some cases, this model can actually perform worse than previous models
    """

    def _get_model(self) -> str:
        return "htdemucs"


class MDXDemucsMusicRemover(DemucsMusicRemover):
    """
    the previous Demucs model
    """

    def _get_model(self) -> str:
        return "mdx_extra_q"


class MusicRemoverModel(str, Enum):
    HT_DEMUCS = "ht_demucs"
    MDX_DEMUCS = "mdx_demucs"

    @property
    def related_class(self) -> Type[MusicRemover]:
        match self:
            case MusicRemoverModel.HT_DEMUCS:
                return HTDemucsMusicRemover
            case MusicRemoverModel.MDX_DEMUCS:
                return MDXDemucsMusicRemover
            case _:
                raise ValueError("Invalid value")
