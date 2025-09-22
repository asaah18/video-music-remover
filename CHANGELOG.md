# Changelog

All notable changes to this project will be documented in this file.

and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Fixed

- Skip failing file processing while batch processing -that happens because the exceptions UnicodeDecodeError and
  RuntimeError- by @asaah18 [#123](https://github.com/asaah18/video-music-remover/pull/123)

## [1.1.2](https://github.com/asaah18/video-music-remover/releases/tag/v1.1.2) - 2025-09-20 - [YANKED]

### Fixed

~~- Skip failing file processing while batch processing -that happens because the exceptions UnicodeDecodeError and
  RuntimeError- by @asaah18 [#123](https://github.com/asaah18/video-music-remover/pull/123)~~

## [1.1.1](https://github.com/asaah18/video-music-remover/releases/tag/1.1.1) - 2025-09-13

### Added

- Added an option to delete original video after processing it and producing the output video by
  @asaah18 [#109](https://github.com/asaah18/video-music-remover/pull/109)
- Added description for CLI command by
  @asaah18 [#110](https://github.com/asaah18/video-music-remover/pull/110)

### Changed

- Used python API of demucs instead of CLI API by
  @asaah18 [#119](https://github.com/asaah18/video-music-remover/pull/119)

### Refactored

- Refactored pre-processing and post-processing prints and logs into events by @asaah18
  in [#120](https://github.com/asaah18/video-music-remover/pull/120)

## [1.0.0](https://github.com/asaah18/video-music-remover/releases/tag/1.0) - 2025-05-24

### Added

- Added CHANGELOG.md file by @asaah18 [#103](https://github.com/asaah18/video-music-remover/pull/103)

### Changed

- Update README.md file to add more content by @asaah18 [#101](https://github.com/asaah18/video-music-remover/pull/101)
- Bump pydantic version from 2.10.6 to 2.11.4 by @asaah18 [#99](https://github.com/asaah18/video-music-remover/pull/99)

### Fixed

- Bump typer version from 0.15.1 to 0.15.4 to fix issue when running the app by
  @asaah18 [#99](https://github.com/asaah18/video-music-remover/pull/99)

## [0.6.0](https://github.com/asaah18/video-music-remover/releases/tag/v0.6) - 2025-05-12

### Added

- Added support for demucs model htdemucs_ft by @asaah18 [#95](https://github.com/asaah18/video-music-remover/pull/95)
- Added support for demucs model htdemucs_ft by @asaah18 [#95](https://github.com/asaah18/video-music-remover/pull/95)
- Added support for demucs model mdx by @asaah18 [#95](https://github.com/asaah18/video-music-remover/pull/95)
- Added support for demucs model mdx_extra by @asaah18 [#95](https://github.com/asaah18/video-music-remover/pull/95)

### Removed

- **(Breaking change)** remove support for model demucs/mdx_extra_q by
  @asaah18 [#94](https://github.com/asaah18/video-music-remover/pull/94)

### Fixed

- Fixed model option autocompletion in music-remove command by
  @asaah18 [#96](https://github.com/asaah18/video-music-remover/pull/96)

### Refactored

- Refactored remove-music and healthcheck commands to use orm for ffmpeg, ffprobe and demucs by @asaah18
  in [#84](https://github.com/asaah18/video-music-remover/pull/84)
- Refactored remove-music command to use return type DemucsModels by @asaah18
  in [#84](https://github.com/asaah18/video-music-remover/pull/84)
- Refactored resolve value of method "_get_default_output_directory" in "DemucsMusicRemover" class by
  @asaah18 [#84](https://github.com/asaah18/video-music-remover/pull/84)

## [0.5.1](https://github.com/asaah18/video-music-remover/releases/tag/v0.5.1) - 2025-04-20

__first release__

### Added

- Added README.md file to describe the project by @asaah18.
- Added LICENSE file by @asaah18.
- Added pyproject.toml to manage the project dependencies by @asaah18.
- Added a CLI command to remove music using AI audio separation from input video file and produce a new
  video without music by @asaah18.
    - The command supports either a supported file or a folder.
    - Supported files are: mp4, mkv and webm.
    - Supported machine learning models are: demucs/htdemucs and demucs/mdx_extra_q.
    - The command has an option to log into a file.
    - The command has an option to choose the AI model to use.
    - Use modular way to observe progress and give feedback.
    - Video without music is saved in output folder directly or in a sub-folder depending on input type(file or folder).
    - Intermediate audio files are stored in a temporary file and cleaned up automatically afterward.
    - All video's audio tracks are processed and replaced.
    - Video's other tracks and metadata are kept intact.
- Added a CLI command for healthcheck with debug option by @asaah18.
- Added a CLI command for checking version by @asaah18.