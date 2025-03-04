import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class MusicRemover(ABC):
    def __init__(self, original_video: Path, output_directory: Optional[Path] = None):
        self._original_video: Path = original_video
        self._output_directory: Path = output_directory if output_directory else self._get_default_output_directory()
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


class DemucsMusicRemover(MusicRemover):
    def _get_default_output_directory(self) -> Path:
        return Path('separated')

    def _get_no_music_audio_path(self, video_path: Path) -> Path:
        return self._output_directory / f'htdemucs/{video_path.stem}/vocals.mp3'

    def remove_music(self) -> None:
        options: list[str] = ['--mp3', '--two-stems=vocals', '-o', self._output_directory.absolute()]
        remove_music_command: list[str] = ['uv', 'run', 'demucs'] + options + [self._original_video.absolute()]
        subprocess.run(remove_music_command, encoding='utf-8', check=True)
        # raise exception if vocal sound is not created
        # exception raised manually because demucs command doesn't return error code
        if not self.no_music_sound.exists():
            raise subprocess.CalledProcessError(returncode=1, cmd=remove_music_command)
