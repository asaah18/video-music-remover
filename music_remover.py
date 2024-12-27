import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


class MusicRemover(ABC):
    def __init__(self, original_video: Path):
        self._original_video: Path = original_video
        self.__no_music_sound: Path = self._get_no_music_audio_path(original_video)

    @property
    def no_music_sound(self) -> Path:
        return self.__no_music_sound

    @abstractmethod
    def _get_no_music_audio_path(self, video_path: Path) -> Path:
        pass

    @abstractmethod
    def remove_music(self) -> None:
        """
        separate vocal from music using machine learning model

        :exception subprocess.CalledProcessError
        """

    pass


class DemucsMusicRemover(MusicRemover):
    def _get_no_music_audio_path(self, video_path: Path) -> Path:
        return Path(f'separated/htdemucs/{video_path.stem}/vocals.mp3')

    def remove_music(self) -> None:
        remove_music_command: list[str] = ['pipenv', 'run', 'demucs', '--mp3', '--two-stems=vocals',
                                           self._original_video.absolute()]
        subprocess.run(remove_music_command, encoding='utf-8', check=True)
        # raise exception if vocal sound is not created
        # exception raised manually because demucs command doesn't return error code
        if not self.no_music_sound.exists():
            raise subprocess.CalledProcessError(returncode=1, cmd=remove_music_command)
