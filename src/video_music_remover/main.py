import logging
import subprocess
from itertools import chain
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Optional, Type

import typer
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    DirectoryPath,
    model_validator,
)
from rich import print as rich_print
from typing_extensions import Self

from video_music_remover.music_remover_models import MusicRemover, MusicRemoverModel

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
        print(f'Processing file "{self.__original_video.name}"')

        # TemporaryDirectory is cleaned up automatically
        with TemporaryDirectory(prefix='music-remover-') as temporary_directory:
            music_remover = self.__music_remover_class(self.__original_video, Path(temporary_directory))

            logging.info(f'"{self.__original_video.name}": start separating vocal...')
            print(f'"{self.__original_video.name}": start separating vocal...')
            music_remover.remove_music()
            logging.info(f'"{self.__original_video.name}": vocal seperated successfully')
            print(f'"{self.__original_video.name}": vocal seperated successfully')

            logging.info(f'"{self.__original_video.name}": creating a new video with no music...')
            print(f'"{self.__original_video.name}": creating a new video with no music...')
            self.__create_video_without_music(music_remover.no_music_sound)
            logging.info(f'"{self.__original_video.name}": a new video with no music has been created')
            print(f'"{self.__original_video.name}": a new video with no music has been created')

            logging.info(f'"{self.__original_video.name}": deleting original video...')
            print(f'"{self.__original_video.name}": deleting original video...')
            self.__cleanup_original_video()
            logging.info(f'"{self.__original_video.name}": original video deleted successfully')
            print(f'"{self.__original_video.name}": original video deleted successfully')

        logging.info(f'"{self.__original_video.name}": Processing finished')
        print(f'"{self.__original_video.name}": Processing finished')

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


def is_supported_file(path: Path) -> bool:
    return path.is_file() and path.suffix in extensions


def is_directories_conflicting(first_path: Path, second_path: Path) -> bool:
    return first_path.is_relative_to(second_path) or second_path.is_relative_to(first_path)


# model

def supported_file(value: Path) -> Path:
    if value.is_file() and not is_supported_file(value):
        raise ValueError('not a supported file type')

    return value


def path_exists(value: Path) -> Path:
    if not value.exists():
        raise ValueError(f'{value} is not an existing path')

    return value


def resolve_path(value: Path) -> Path:
    """
    resolve path instance

    :raises FileNotFoundError if path does not exist
    """
    return value.resolve(True)


class MusicRemoverData(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', frozen=True)

    input_path: Annotated[
        Path, AfterValidator(path_exists), AfterValidator(resolve_path), AfterValidator(supported_file)]
    output_path: Annotated[DirectoryPath, AfterValidator(resolve_path)]

    @model_validator(mode='after')
    def conflicting_directories(self) -> Self:
        if is_directories_conflicting(self.input_path, self.output_path):
            raise ValueError('output path should not be a child or a parent or an exact of the input path')
        return self


# process file/s

def get_original_video(input_path: Path) -> Path | None:
    logging.info(f'Looking for file to process in folder "{input_path.absolute()}"...')
    print(f'Looking for file to process in folder "{input_path.absolute()}"...')
    iterable = chain.from_iterable(input_path.rglob(f"*{ext}") for ext in extensions)

    return next(iterable, None)


def process_files(music_remover_data: MusicRemoverData, model: Type[MusicRemover]) -> None:
    if music_remover_data.input_path.is_dir():
        logging.info('Mass processing started')
        print('Mass processing started')

        while original_video := get_original_video(music_remover_data.input_path):
            RemoveMusicFromVideo(
                original_video=original_video.resolve(),
                music_remover_class=model,
                output_directory=music_remover_data.output_path,
                base_directory=music_remover_data.input_path
            ).process()
        else:
            logging.info("There's no file to process")
            print("There's no file to process")

        logging.info('Mass processing finished')
        print('Mass processing finished')
    else:
        # input is an existing file
        RemoveMusicFromVideo(
            original_video=music_remover_data.input_path,
            music_remover_class=model,
            output_directory=music_remover_data.output_path
        ).process()


# CLI code

def cli_supported_file(ctx: typer.Context, value: Path) -> Path | None:
    """
    :raises typer.BadParameter with a message clarifying the error
    """
    if ctx.resilient_parsing:
        return None

    if supported_file(value):
        return value
    else:
        raise typer.BadParameter('not a supported file type')


def cli_conflicting_directories(ctx: typer.Context, output_path: Path) -> Path | None:
    """
    :raises typer.BadParameter with a message clarifying the error
    """
    if ctx.resilient_parsing:
        return None

    if not is_directories_conflicting(ctx.params['input_path'], output_path):
        return output_path
    else:
        raise typer.BadParameter("can't be a parent or a child or an exact directory of input_path")


def cli_is_log_file(ctx: typer.Context, value: Optional[Path]) -> Path | None:
    """
    :raises typer.BadParameter with a message clarifying the error
    """
    if ctx.resilient_parsing:
        return None

    if value and value.suffix != ".log":
        raise typer.BadParameter("must be a log file")
    else:
        return value


@app.command()
def remove_music(
        input_path: Annotated[
            Path, typer.Argument(
                help="file or directory to remove music from",
                exists=True,
                callback=cli_supported_file,
                resolve_path=True
            )
        ],
        output_path: Annotated[
            Path, typer.Argument(
                help="the directory where video without music is stored",
                exists=True,
                file_okay=False,
                callback=cli_conflicting_directories,
                resolve_path=True
            )
        ],
        log: Annotated[
            Path, typer.Option(
                help="the logging file, if not passed no log will be created",
                callback=cli_is_log_file,
                resolve_path=True
            )
        ] = None,
        model: Annotated[
            MusicRemoverModel, typer.Option(help='the machine learning model to use')] = MusicRemoverModel.HT_DEMUCS
):
    """
    remove music from a directory with videos or a single video
    """
    logging.basicConfig(
        filename=log,
        encoding='utf-8',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    process_files(MusicRemoverData(input_path=input_path, output_path=output_path), model=model.related_class)


@app.command()
def health_check(debug: Annotated[bool, typer.Option("--debug")] = False) -> None:
    capture_output = not debug
    has_error = False

    def print_debug(message: str) -> None:
        rich_print(f'[bold blue][DEBUG] {message}[/bold blue]')

    def print_error(message: str, prefix: bool) -> None:
        rich_print(f"[bold red]{'[ERROR] ' if prefix else ''}{message}[/bold red]")

    def print_info(message: str) -> None:
        rich_print(f"[bold green][INFO] {message}[/bold green]")

    def print_success(message: str) -> None:
        rich_print(f"[bold green]{message}[/bold green]")

    # ffmpeg
    if debug:
        print_debug('running command "ffmpeg -version"')
    if subprocess.run(["ffmpeg", "-version"], encoding='utf-8', capture_output=capture_output).returncode != 0:
        print_error('ffmpeg not installed', prefix=True)
        has_error = True
    else:
        print_info("ffmpeg installed")

    # demucs machine learning model
    if debug:
        print_debug('running command "uv run demucs -h"')
    if subprocess.run(['uv', 'run', 'demucs', '-h'], encoding='utf-8', capture_output=capture_output).returncode != 0:
        print_error("demucs not installed", prefix=True)
        has_error = True
    else:
        print_info("demucs installed")

    if has_error:
        print_error('There are some issues', prefix=False)
        exit(1)
    else:
        print_success('Everything is ok')


if __name__ == "__main__":
    app()
