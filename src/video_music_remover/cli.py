import importlib.metadata
import importlib.util
import logging
import subprocess
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import print as rich_print

from video_music_remover.common import is_directories_conflicting, supported_file
from video_music_remover.main import MusicRemoverData, process_files
from video_music_remover.music_remover_models import MusicRemoverModel
from video_music_remover.orms.ffmpeg import FfmpegBuilder, FfprobeBuilder

app = typer.Typer(
    help="A powerful Python tool to remove music from videos while preserving speech and other sounds using advanced machine learning models"
)


def cli_supported_file(ctx: typer.Context, value: Path) -> Path | None:
    """
    :raises typer.BadParameter with a message clarifying the error
    """
    if ctx.resilient_parsing:
        return None

    if supported_file(value):
        return value
    else:
        raise typer.BadParameter("not a supported file type")


def cli_conflicting_directories(ctx: typer.Context, output_path: Path) -> Path | None:
    """
    :raises typer.BadParameter with a message clarifying the error
    """
    if ctx.resilient_parsing:
        return None

    if not is_directories_conflicting(ctx.params["input_path"], output_path):
        return output_path
    else:
        raise typer.BadParameter(
            "can't be a parent or a child or an exact directory of input_path"
        )


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


def print_debug(message: str) -> None:
    rich_print(f"[bold blue][DEBUG] {message}[/bold blue]")


def print_error(message: str, prefix: bool) -> None:
    rich_print(f"[bold red]{'[ERROR] ' if prefix else ''}{message}[/bold red]")


def print_info(message: str) -> None:
    rich_print(f"[bold green][INFO] {message}[/bold green]")


def print_success(message: str) -> None:
    rich_print(f"[bold green]{message}[/bold green]")


def autocompletion(incomplete: str):
    for name, help_text in MusicRemoverModel.autocompletion():
        if name.startswith(incomplete):
            yield (name, help_text)


@app.command()
def remove_music(
    input_path: Annotated[
        Path,
        typer.Argument(
            help="file or directory to remove music from",
            exists=True,
            callback=cli_supported_file,
            resolve_path=True,
        ),
    ],
    output_path: Annotated[
        Path,
        typer.Argument(
            help="the directory where video without music is stored",
            exists=True,
            file_okay=False,
            callback=cli_conflicting_directories,
            resolve_path=True,
        ),
    ],
    log: Annotated[
        Path,
        typer.Option(
            help="the logging file, if not passed no log will be created",
            callback=cli_is_log_file,
            resolve_path=True,
        ),
    ] = None,
    model: Annotated[
        MusicRemoverModel,
        typer.Option(
            help="the machine learning model to use", autocompletion=autocompletion
        ),
    ] = MusicRemoverModel.HT_DEMUCS,
    delete_original: Annotated[
        bool,
        typer.Option(
            help="delete original file after processing it and producing the output video"
        ),
    ] = False,
):
    """
    remove music from a directory with videos or a single video
    """
    logger = None

    if log:
        logger = logging.getLogger("music_remover")
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(filename=log, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        logger.addHandler(file_handler)

    process_files(
        music_remover_data=MusicRemoverData(
            input_path=input_path, output_path=output_path
        ),
        model=model.related_class,
        logger=logger,
        delete_original=delete_original,
    )


@app.command()
def health_check(debug: Annotated[bool, typer.Option("--debug")] = False) -> None:
    """check if the tool is installed properly -including system dependencies-"""
    capture_output = not debug
    has_error = False

    # ffmpeg
    ffmpeg_builder = FfmpegBuilder.health_check()

    if debug:
        print_debug(f'running command "{ffmpeg_builder.command}"')
    if (
        subprocess.run(
            ffmpeg_builder.command, encoding="utf-8", capture_output=capture_output
        ).returncode
        != 0
    ):
        print_error("ffmpeg not installed", prefix=True)
        has_error = True
    else:
        print_info("ffmpeg installed")

    # ffprobe
    ffprobe_builder = FfprobeBuilder.health_check()

    if debug:
        print_debug(f'running command "{ffprobe_builder.command}"')

    if (
        subprocess.run(
            ffprobe_builder.command, encoding="utf-8", capture_output=capture_output
        ).returncode
        != 0
    ):
        print_error("ffprobe not installed", prefix=True)
        has_error = True
    else:
        print_info("ffprobe installed")

    # demucs machine learning model, healthcheck by trying to import demucs
    if debug:
        print_debug('trying to import "demucs"')

    if importlib.util.find_spec("demucs"):
        print_info("demucs installed")
    else:
        print_error("demucs not installed", prefix=True)
        has_error = True

    if has_error:
        print_error("There are some issues", prefix=False)
        exit(1)
    else:
        print_success("Everything is ok")


@app.command()
def version() -> None:
    print(importlib.metadata.version("video-music-remover"))


if __name__ == "__main__":
    app()
