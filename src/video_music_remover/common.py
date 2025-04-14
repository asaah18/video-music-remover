from pathlib import Path
from typing import Callable

extensions = (".mp4", ".mkv", ".webm")


def is_supported_file(path: Path) -> bool:
    return path.is_file() and path.suffix in extensions


def supported_file(value: Path) -> Path:
    if value.is_file() and not is_supported_file(value):
        raise ValueError("not a supported file type")

    return value


def resolve_path_factory(strict: bool) -> Callable[[Path], Path]:
    """
    resolve path instance

    :raises FileNotFoundError if path does not exist when strict is True
    """

    def resolve(value: Path) -> Path:
        return value.resolve(strict=strict)

    return resolve


def resolve_paths_factory(strict: bool) -> Callable[[list[Path]], list[Path]]:
    """
    resolve path instances

    :raises FileNotFoundError if path does not exist when strict is True
    """

    def resolve(values: list[Path]) -> list[Path]:
        return [value.resolve(strict=strict) for value in values]

    return resolve


def is_directories_conflicting(first_path: Path, second_path: Path) -> bool:
    return first_path.is_relative_to(second_path) or second_path.is_relative_to(
        first_path
    )
