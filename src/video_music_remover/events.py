import logging
from abc import ABC, abstractmethod
from pathlib import Path


class MusicRemoverObserver(ABC):
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
    def video_processing_finished(self, original_video: Path, new_video: Path) -> None:
        pass

    @abstractmethod
    def delete_original_video_started(self, original_video: Path) -> None:
        pass

    @abstractmethod
    def delete_original_video_finished(self, original_video: Path) -> None:
        pass


class MusicRemoveEventDispatcher:
    def __init__(self, observers: list[MusicRemoverObserver] = None) -> None:
        self.__observers: list[MusicRemoverObserver] = observers if observers else []

    def attach(self, observer: MusicRemoverObserver) -> None:
        self.__observers.append(observer)

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


# observers
class LogObserver(MusicRemoverObserver):
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

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


class PrintObserver(MusicRemoverObserver):
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
