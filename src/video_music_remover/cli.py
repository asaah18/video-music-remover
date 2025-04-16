import logging
import subprocess
from pathlib import Path
from typing import Optional, Annotated

import typer
from rich import print as rich_print

from video_music_remover.common import (
    supported_file,
    is_directories_conflicting,
    MusicRemoverData,
)
from video_music_remover.main import process_files
from video_music_remover.music_remover_models import MusicRemoverModel

app = typer.Typer()


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
        MusicRemoverModel, typer.Option(help="the machine learning model to use")
    ] = MusicRemoverModel.HT_DEMUCS,
):
    """
    remove music from a directory with videos or a single video
    """
    logging.basicConfig(
        filename=log,
        encoding="utf-8",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    process_files(
        MusicRemoverData(input_path=input_path, output_path=output_path),
        model=model.related_class,
    )


@app.command()
def health_check(debug: Annotated[bool, typer.Option("--debug")] = False) -> None:
    capture_output = not debug
    has_error = False

    # ffmpeg
    if debug:
        print_debug('running command "ffmpeg -version"')
    if (
        subprocess.run(
            ["ffmpeg", "-version"], encoding="utf-8", capture_output=capture_output
        ).returncode
        != 0
    ):
        print_error("ffmpeg not installed", prefix=True)
        has_error = True
    else:
        print_info("ffmpeg installed")

    # ffprobe
    if debug:
        print_debug('running command "ffprobe -version"')
    if (
        subprocess.run(
            ["ffprobe", "-version"], encoding="utf-8", capture_output=capture_output
        ).returncode
        != 0
    ):
        print_error("ffprobe not installed", prefix=True)
        has_error = True
    else:
        print_info("ffprobe installed")

    # demucs machine learning model
    if debug:
        print_debug('running command "uv run demucs -h"')

    ffmpeg_health_check = subprocess.run(
        ["demucs", "-h"], encoding="utf-8", capture_output=capture_output
    )
    if ffmpeg_health_check.returncode != 0:
        print_error("demucs not installed", prefix=True)
        has_error = True
    else:
        print_info("demucs installed")

    if has_error:
        print_error("There are some issues", prefix=False)
        exit(1)
    else:
        print_success("Everything is ok")


if __name__ == "__main__":
    app()
