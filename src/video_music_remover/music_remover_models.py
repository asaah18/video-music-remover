import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Optional, Type

from pydantic import DirectoryPath, FilePath, validate_call

from video_music_remover.orms import DemucsBuilder, DemucsModels


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
    def _get_model(self) -> DemucsModels:
        """
        the models to choose from are: htdemucs, mdx_extra_q
        """
        pass

    def _get_default_output_directory(self) -> Path:
        return Path("separated").resolve()

    def _get_no_music_audio_path(self, video_path: Path) -> Path:
        return self._output_directory.joinpath(
            f"{self._get_model()}/{video_path.stem}/vocals.mp3"
        )

    def remove_music(self) -> None:
        demucs_builder = DemucsBuilder(self._original_video)
        demucs_builder.save_as("mp3")
        demucs_builder.two_stems("vocals")
        demucs_builder.model(self._get_model())
        demucs_builder.output_directory(self._output_directory)

        remove_music_command: list[str] = demucs_builder.command

        subprocess.run(remove_music_command, encoding="utf-8", check=True)
        # raise exception if vocal sound is not created
        # exception raised manually because demucs command doesn't return error code
        if not self.no_music_sound.exists():
            raise subprocess.CalledProcessError(returncode=1, cmd=remove_music_command)


class HTDemucsMusicRemover(DemucsMusicRemover):
    """
    first version of Hybrid Transformer Demucs.

    Trained on MusDB + 800 songs. Default model
    """

    def _get_model(self) -> DemucsModels:
        return "htdemucs"


class HTDemucsFTMusicRemover(DemucsMusicRemover):
    """
    fine-tuned version of htdemucs, separation will take 4 times more time but might be a bit better.

    Same training set as htdemucs.
    """

    def _get_model(self) -> DemucsModels:
        return "htdemucs_ft"


class MDXDemucsMusicRemover(DemucsMusicRemover):
    """
    trained only on MusDB HQ, winning model on track A at the MDX challenge.
    """

    def _get_model(self) -> DemucsModels:
        return "mdx"


class MDXExtraDemucsMusicRemover(DemucsMusicRemover):
    """
    trained with extra training data (including MusDB test set), ranked 2nd on the track B of the MDX challenge.
    """

    def _get_model(self) -> DemucsModels:
        return "mdx_extra"


class MusicRemoverModel(str, Enum):
    HT_DEMUCS = "ht_demucs"
    HT_DEMUCS_FT = "ht_demucs_ft"
    MDX_DEMUCS = "mdx_demucs"
    MDX_EXTRA_DEMUCS = "mdx_extra_demucs"

    @property
    def related_class(self) -> Type[MusicRemover]:
        match self:
            case MusicRemoverModel.HT_DEMUCS:
                return HTDemucsMusicRemover
            case MusicRemoverModel.HT_DEMUCS_FT:
                return HTDemucsFTMusicRemover
            case MusicRemoverModel.MDX_DEMUCS:
                return MDXDemucsMusicRemover
            case MusicRemoverModel.MDX_EXTRA_DEMUCS:
                return MDXExtraDemucsMusicRemover
            case _:
                raise ValueError("Invalid value")

    @staticmethod
    def autocompletion() -> list[tuple[str, str]]:
        """
        CLI autocompletion

        :returns a list of tuples with name and description
        """
        return [
            (
                MusicRemoverModel.HT_DEMUCS.value,
                "demucs model | first version of Hybrid Transformer Demucs",
            ),
            (
                MusicRemoverModel.HT_DEMUCS_FT.value,
                "demucs model | fine-tuned version of htdemucs, separation will take 4 times more time but might be a bit better",
            ),
            (
                MusicRemoverModel.MDX_DEMUCS.value,
                "demucs model | trained only on MusDB HQ, winning model on track A at the MDX challenge",
            ),
            (
                MusicRemoverModel.MDX_EXTRA_DEMUCS.value,
                "demucs model | trained with extra training data (including MusDB test set), ranked 2nd on the track B of the MDX challenge",
            ),
        ]
