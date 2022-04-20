import logging
from datetime import datetime
from utils.Singleton import Singleton


class Logger(metaclass=Singleton):
    def __init__(self):
        self._logger = logging.getLogger()
        self._logger.setLevel(level=logging.DEBUG)

        current_time = datetime.now()
        date_time = current_time.strftime("%m.%d.%Y_%H.%M.%S")

        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(f'logs/emotion_recognition_{date_time}.log')

        console_handler.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)

        message_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        console_format = logging.Formatter(message_format)
        file_format = logging.Formatter(message_format)

        console_handler.setFormatter(console_format)
        file_handler.setFormatter(file_format)

        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)

    def log_info(self, message):
        self._logger.info(message)

    def log_debug(self, message):
        self._logger.debug(message)

    def log_warning(self, message):
        self._logger.warning(message)

    def log_error(self, message):
        self._logger.error(message)

    def log_critical(self, message):
        self._logger.critical(message)
