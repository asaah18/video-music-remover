import logging
from abc import ABC, abstractmethod
from pathlib import Path


class MusicRemoverObserver(ABC):
    @abstractmethod
    def mass_processing_started(self, directory: Path) -> None:
        pass

    @abstractmethod
    def video_processing_started(self, original_video: Path) -> None:
        pass

    @abstractmethod
    def audio_processing_started(
        self, original_video: Path, counter: int, total: int
    ) -> None:
        pass

    @abstractmethod
    def audio_processing_finished(
        self, original_video: Path, counter: int, total: int
    ) -> None:
        pass

    @abstractmethod
    def creating_new_video_started(self, original_video: Path, new_video: Path) -> None:
        pass

    @abstractmethod
    def creating_new_video_finished(
        self, original_video: Path, new_video: Path
    ) -> None:
        pass

    @abstractmethod
    def skipping_failed_file(self, original_video: Path, exception: Exception) -> None:
        pass

    @abstractmethod
    def video_processing_finished(self, original_video: Path, new_video: Path) -> None:
        pass

    @abstractmethod
    def delete_original_video_started(self, original_video: Path) -> None:
        pass

    @abstractmethod
    def delete_original_video_finished(self, original_video: Path) -> None:
        pass

    @abstractmethod
    def mass_processing_finished(self, directory: Path) -> None:
        pass


class MusicRemoveEventDispatcher:
    def __init__(self, observers: list[MusicRemoverObserver] = None) -> None:
        self.__observers: list[MusicRemoverObserver] = observers if observers else []

    def attach(self, observer: MusicRemoverObserver) -> None:
        self.__observers.append(observer)

    def mass_processing_started(self, directory: Path) -> None:
        for observer in self.__observers:
            observer.mass_processing_started(directory=directory)

    def video_processing_started(self, original_video: Path) -> None:
        for observer in self.__observers:
            observer.video_processing_started(original_video=original_video)

    def audio_processing_started(
        self, original_video: Path, counter: int, total: int
    ) -> None:
        for observer in self.__observers:
            observer.audio_processing_started(
                original_video=original_video, counter=counter, total=total
            )

    def audio_processing_finished(
        self, original_video: Path, counter: int, total: int
    ) -> None:
        for observer in self.__observers:
            observer.audio_processing_finished(
                original_video=original_video, counter=counter, total=total
            )

    def creating_new_video_started(self, original_video: Path, new_video: Path) -> None:
        for observer in self.__observers:
            observer.creating_new_video_started(
                original_video=original_video, new_video=new_video
            )

    def creating_new_video_finished(
        self, original_video: Path, new_video: Path
    ) -> None:
        for observer in self.__observers:
            observer.creating_new_video_finished(
                original_video=original_video, new_video=new_video
            )

    def skipping_failed_file(self, original_video: Path, exception: Exception) -> None:
        for observer in self.__observers:
            observer.skipping_failed_file(
                original_video=original_video, exception=exception
            )

    def video_processing_finished(self, original_video: Path, new_video: Path) -> None:
        for observer in self.__observers:
            observer.video_processing_finished(
                original_video=original_video, new_video=new_video
            )

    def delete_original_video_started(self, original_video: Path) -> None:
        for observer in self.__observers:
            observer.delete_original_video_started(original_video=original_video)

    def delete_original_video_finished(self, original_video: Path) -> None:
        for observer in self.__observers:
            observer.delete_original_video_finished(original_video=original_video)

    def mass_processing_finished(self, directory: Path) -> None:
        for observer in self.__observers:
            observer.mass_processing_finished(directory=directory)


# observers
class LogObserver(MusicRemoverObserver):
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def mass_processing_started(self, directory: Path) -> None:
        self.logger.info("Mass processing started")

    def video_processing_started(self, original_video: Path) -> None:
        self.logger.info(f'Processing file "{original_video.name}"')

    def audio_processing_started(
        self, original_video: Path, counter: int, total: int
    ) -> None:
        self.logger.info(
            f'"{original_video.name}": start separating vocal... {counter}/{total}'
        )

    def audio_processing_finished(
        self, original_video: Path, counter: int, total: int
    ) -> None:
        self.logger.info(
            f'"{original_video.name}": vocal seperated successfully {counter}/{total}'
        )

    def creating_new_video_started(self, original_video: Path, new_video: Path) -> None:
        self.logger.info(
            f'"{original_video.name}": creating a new video with no music...'
        )

    def creating_new_video_finished(
        self, original_video: Path, new_video: Path
    ) -> None:
        self.logger.info(
            f'"{original_video.name}": a new video with no music has been created'
        )

    def skipping_failed_file(self, original_video: Path, exception: Exception) -> None:
        self.logger.error(
            f"a cli error occurred while processing file {original_video}, skipping the file. error: {exception}"
        )

    def video_processing_finished(self, original_video: Path, new_video: Path) -> None:
        self.logger.info(f'"{original_video.name}": Processing finished')

    def delete_original_video_started(self, original_video: Path) -> None:
        self.logger.info(
            f'"{original_video.name}": Post-Processing(optional): deleting original video...'
        )

    def delete_original_video_finished(self, original_video: Path) -> None:
        self.logger.info(
            f'"{original_video.name}": Post-Processing(optional): original video deleted successfully'
        )

    def mass_processing_finished(self, directory: Path) -> None:
        self.logger.info("Mass processing finished")


class PrintObserver(MusicRemoverObserver):
    def mass_processing_started(self, directory: Path) -> None:
        print("Mass processing started")

    def video_processing_started(self, original_video: Path) -> None:
        print(f'Processing file "{original_video.name}"')

    def audio_processing_started(
        self, original_video: Path, counter: int, total: int
    ) -> None:
        print(f'"{original_video.name}": start separating vocal... {counter}/{total}')

    def audio_processing_finished(
        self, original_video: Path, counter: int, total: int
    ) -> None:
        print(
            f'"{original_video.name}": vocal seperated successfully {counter}/{total}'
        )

    def creating_new_video_started(self, original_video: Path, new_video: Path) -> None:
        print(f'"{original_video.name}": creating a new video with no music...')

    def creating_new_video_finished(
        self, original_video: Path, new_video: Path
    ) -> None:
        print(f'"{original_video.name}": a new video with no music has been created')

    def skipping_failed_file(self, original_video: Path, exception: Exception) -> None:
        print(
            f"a cli error occurred while processing file {original_video}, skipping the file. error: {exception}"
        )

    def video_processing_finished(self, original_video: Path, new_video: Path) -> None:
        print(f'"{original_video.name}": Processing finished')

    def delete_original_video_started(self, original_video: Path) -> None:
        print(
            f'"{original_video.name}": Post-Processing(optional): deleting original video...'
        )

    def delete_original_video_finished(self, original_video: Path) -> None:
        print(
            f'"{original_video.name}": Post-Processing(optional): original video deleted successfully'
        )

    def mass_processing_finished(self, directory: Path) -> None:
        print("Mass processing finished")
