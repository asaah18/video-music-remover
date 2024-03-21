import logging
import subprocess
import sys
from pathlib import Path


def process_file(original_video: Path):
    """
    removes music from videos in input folder
    :return: True if there's no file to process, which marks the end of the mass process
    """
    try:
        logging.info(f'Processing file "{original_video.name}"')

        no_music_sound: Path = Path(f'separated/htdemucs/{original_video.stem}/vocals.mp3')
        if no_music_sound.exists():
            logging.info(f'"{original_video.name}": vocal already separated, skipping separating vocal')
        else:
            logging.info(f'"{original_video.name}": start separating vocal...')
            # TODO: export vocal sound as `wav` extension
            remove_music_command: list[str] = ['pipenv', 'run', 'demucs', '--mp3', '--two-stems=vocals',
                                               original_video.absolute()]
            completed_process = subprocess.run(remove_music_command, encoding='utf-8', text=True,
                                               capture_output=True,
                                               check=True)
            # raise exception if vocal sound is not created, exception raised manually
            # because demucs command doesn't return error code
            if not no_music_sound.exists():
                raise subprocess.CalledProcessError(returncode=1,
                                                    cmd=completed_process.args,
                                                    output=completed_process.stdout,
                                                    stderr=completed_process.stderr)
            logging.info(f'"{original_video.name}": vocal seperated successfully')
        # 3- replace the sound of the video with the no music version,
        #  and save the new video in folder 'output'
        #  if not already done
        no_music_video: Path = Path(f'output/{original_video.name}')
        if no_music_video.exists():
            logging.info(
                f'"{original_video.name}": a video with no music already exists, skipping creating a new video')
        else:
            logging.info(f'"{original_video.name}": creating a new video with no music...')
            create_no_music_video_command: list[str] = ['ffmpeg', '-i', original_video.absolute(),
                                                        '-i', no_music_sound.absolute(),
                                                        '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0',
                                                        no_music_video.absolute()]
            subprocess.run(create_no_music_video_command, encoding='utf-8', text=True, capture_output=True, check=True)
            logging.info(f'"{original_video.name}": a new video with no music has been created')
        # clean up
        logging.info(f'"{original_video.name}": deleting original video...')
        original_video.unlink()
        logging.info(f'"{original_video.name}": original video deleted successfully')
        logging.info(f'"{original_video.name}": deleting vocal sound...')
        for file in [file for file in no_music_sound.parent.iterdir()]:
            file.unlink()
        no_music_sound.parent.rmdir()
        logging.info(f'"{original_video.name}": vocal sound deleted successfully')
    except subprocess.CalledProcessError as error:
        logging.exception(error.stderr)
        raise error
    except KeyboardInterrupt as error:
        logging.exception('the process was stopped by user')
        raise error
    except BaseException as error:
        logging.exception('Unexpected error happened')
        raise error
    else:
        logging.info(f'"{original_video.name}": Processing finished')


def get_original_video() -> Path | None:
    logging.info('Looking for file to process in folder "input"...')
    input_path: Path = Path('input')
    return next(input_path.glob("*.mp4"), None)


def main() -> None:
    logging.basicConfig(
        encoding='utf-8',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler("removing_music.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.info('Mass processing started')

    while original_video := get_original_video():
        process_file(original_video)
    else:
        logging.info("There's no file to process")

    logging.info('Mass processing finished')


if __name__ == "__main__":
    # encapsulating the code of this block in a function ensures that scope of variables is not global
    sys.exit(main())
