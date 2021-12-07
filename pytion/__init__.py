import logging
from typing import Optional, Union

import pytion.envs as envs
from pytion.api import Notion


def setup_logging(
        level: Union[int, str] = logging.INFO, to_console: bool = True, filename: Optional[str] = None
) -> None:
    """

    :param level:       "debug", "info", "warning", "error", "critical" or `logging.INFO` etc.
    :param to_console:  True/False to output to stdout
    :param filename:    filename to put logs into file. or None
    :return:
    """
    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    if isinstance(level, str):
        if level not in log_levels:
            raise ValueError("Invalid log level")
        level = log_levels[level]
    logger = logging.getLogger(__name__)
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    if filename:
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


setup_logging(level=envs.LOGGING_BASE_LEVEL, to_console=envs.LOGGING_TO_CONSOLE, filename=envs.LOGGING_FILE)

no = Notion()
