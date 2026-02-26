# This Module contains logging code
import logging
import os
from queue import SimpleQueue
from threading import Lock
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler


# Logger creation
logger = logging.getLogger(name="logtalk2db")
logger.setLevel(level=logging.DEBUG)
logger.propagate = False

_init_lock = Lock()
_queue_listener = None
_initialized = False


# Project Loggers
def custom_logging():
    """Configure async queue-based logging to avoid clashes under high concurrency."""
    global _queue_listener, _initialized

    if _initialized:
        return logger

    with _init_lock:
        if _initialized:
            return logger

        if logger.handlers:
            logger.handlers.clear()

        log_path = os.path.join(os.path.dirname(__file__), "log.log")
        formatter = logging.Formatter(
            "%(asctime)s-%(name)s-%(levelname)s-%(threadName)s-%(message)s"
        )

        file_handler = RotatingFileHandler(
            filename=log_path,
            mode="a",
            maxBytes=20 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)

        log_queue = SimpleQueue()
        queue_handler = QueueHandler(log_queue)
        queue_handler.setLevel(logging.DEBUG)
        logger.addHandler(queue_handler)

        _queue_listener = QueueListener(
            log_queue,
            file_handler,
            stream_handler,
            respect_handler_level=True,
        )
        _queue_listener.start()

        _initialized = True
        return logger


def shutdown_logging():
    """Gracefully stop the logging listener."""
    global _queue_listener, _initialized
    with _init_lock:
        if _queue_listener is not None:
            _queue_listener.stop()
            _queue_listener = None
        _initialized = False

logger=custom_logging()

if __name__ == "__main__":
    custom_logging()

    
