import errno
import logging
import subprocess
import sys
from itertools import chain
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Type, Annotated, Optional

import typer

from custom_exceptions import UnsupportedFileError, DirectoriesConflictError
from music_remover import MusicRemover, DemucsMusicRemover

app = typer.Typer()


class RemoveMusicFromVideo:
    def __init__(
            self,
            original_video: Path,
            music_remover_class: Type[MusicRemover],
            output_directory: Path,
            base_directory: Optional[Path] = None
    ):
        """:raise ValueError if base directory is not a relative path of original video or not an absolute path"""
        self.__original_video = original_video
        self.__music_remover_class = music_remover_class
        self.__no_music_video = output_directory / (original_video.relative_to(
            base_directory) if base_directory else original_video.name)

    def process(self) -> None:
        logging.info(f'Processing file "{self.__original_video.name}"')

        # TemporaryDirectory is cleaned up automatically
        with TemporaryDirectory(prefix='music-remover-') as temporary_directory:
            music_remover = self.__music_remover_class(self.__original_video, Path(temporary_directory))

            logging.info(f'"{self.__original_video.name}": start separating vocal...')
            music_remover.remove_music()
            logging.info(f'"{self.__original_video.name}": vocal seperated successfully')

            logging.info(f'"{self.__original_video.name}": creating a new video with no music...')
            self.__create_video_without_music(music_remover.no_music_sound)
            logging.info(f'"{self.__original_video.name}": a new video with no music has been created')

            logging.info(f'"{self.__original_video.name}": deleting original video...')
            self.__cleanup_original_video()
            logging.info(f'"{self.__original_video.name}": original video deleted successfully')

        logging.info(f'"{self.__original_video.name}": Processing finished')

    def __create_video_without_music(self, no_music_sound: Path) -> None:
        """
        replace the sound of the video with the no music version,
        and save the new video in the output folder
        regardless of the existence of the new video
        """
        # there's no check for the existence of new video with no music because it should be overwritten even if it exists
        # to ensure that no incomplete video is being created if the process failed in the middle of the process
        # assuming that original video is deleted by cleanup process when a video without music is created successfully

        # create missing directories in the path if exists
        self.__no_music_video.parent.mkdir(parents=True, exist_ok=True)

        # create video without music
        create_no_music_video_command: list[str] = ['ffmpeg', '-y', '-i', self.__original_video.absolute(),
                                                    '-i', no_music_sound.absolute(),
                                                    '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0',
                                                    self.__no_music_video.absolute()]
        subprocess.run(create_no_music_video_command, encoding='utf-8', check=True)

    def __cleanup_original_video(self) -> None:
        self.__original_video.unlink()


extensions = (".mp4", ".mkv", ".webm")


def is_supported_file(file: Path) -> bool:
    return file.suffix in extensions


def get_original_video(input_path: Path) -> Path | None:
    logging.info(f'Looking for file to process in folder "{input_path.absolute()}"...')
    iterable = chain.from_iterable(input_path.rglob(f"*{ext}") for ext in extensions)

    return next(iterable, None)


def validate_input_path(input_path: Path) -> None:
    """
    :raises FileNotFoundError
    :raises UnsupportedFileError
    """
    if not input_path.exists():
        raise FileNotFoundError(errno.ENOENT, 'No folder or file exists at the location specified',
                                input_path.resolve())

    if input_path.is_file() and not is_supported_file(input_path):
        raise UnsupportedFileError('this file is not a supported file type', input_path.resolve())


def validate_output_path(output_path: Path, input_path: Path) -> None:
    """
    output path should be an existing directory which is not a parent or a child or an exact directory of input_path
    :raises FileNotFoundError if output_path does not exist
    :raises NotADirectoryError if output_path is not a directory
    :raises DirectoriesConflictError if output_path is a parent or a child or an exact directory of input_path
    """
    if not output_path.exists():
        raise FileNotFoundError(errno.ENOENT, 'No folder or file exists at the location specified',
                                output_path.resolve())
    if output_path.is_file():
        raise NotADirectoryError(errno.ENOTDIR, 'output path should not be a file', output_path.resolve())
    if input_path.is_relative_to(output_path) or output_path.is_relative_to(input_path):
        raise DirectoriesConflictError("output_Path should not be a child or a parent or an exact of the input path",
                                       input_path.resolve(), output_path.resolve())


def process_files(input_path: Path, output_path: Path) -> None:
    validate_input_path(input_path)
    validate_output_path(output_path=output_path, input_path=input_path)

    if input_path.is_dir():
        logging.info('Mass processing started')

        while original_video := get_original_video(input_path):
            RemoveMusicFromVideo(
                original_video=original_video.resolve(),
                music_remover_class=DemucsMusicRemover,
                output_directory=output_path,
                base_directory=input_path.resolve()
            ).process()
        else:
            logging.info("There's no file to process")

        logging.info('Mass processing finished')
    else:
        # input is an existing file
        RemoveMusicFromVideo(
            original_video=input_path.resolve(),
            music_remover_class=DemucsMusicRemover,
            output_directory=output_path
        ).process()


# CLI code

def cli_validate_input_path(ctx: typer.Context, input_path: Path) -> Path | None:
    """
    :raises typer.BadParameter with a message clarifying the error
    """
    if ctx.resilient_parsing:
        return None

    try:
        validate_input_path(input_path)
        return input_path
    except UnsupportedFileError:
        raise typer.BadParameter('not a supported file type')


def cli_validate_output_path(ctx: typer.Context, output_path: Path) -> Path | None:
    """
    :raises typer.BadParameter with a message clarifying the error
    """
    if ctx.resilient_parsing:
        return None

    try:
        validate_output_path(output_path=output_path, input_path=ctx.params['input_path'])
        return output_path
    except DirectoriesConflictError:
        raise typer.BadParameter("can't be a parent or a child or an exact directory of input_path")


@app.command()
def main(
        input_path: Annotated[
            Path, typer.Argument(help="file or directory to remove music from",
                                 callback=cli_validate_input_path,
                                 exists=True,
                                 resolve_path=True)],
        output_path: Annotated[
            Path, typer.Argument(help="the directory where video without music is stored",
                                 exists=True,
                                 file_okay=False,
                                 callback=cli_validate_output_path,
                                 resolve_path=True)]
):
    """
    remove music from a directory with videos or a single video
    """
    logging.basicConfig(
        encoding='utf-8',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler("removing_music.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    process_files(input_path=input_path, output_path=output_path)


if __name__ == "__main__":
    app()
