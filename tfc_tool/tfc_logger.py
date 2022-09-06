import logging


def new(debug: bool):
    logger = logging.Logger(name="tfc")
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel("INFO" if not debug else "DEBUG")
    if debug:
        # prettier-ignore
        stdout_handler.setFormatter(
            fmt=logging.Formatter("[%(levelname)s] [%(name)s] - %(message)s")
        )
    else:
        stdout_handler.setFormatter(
            fmt=logging.Formatter("[%(levelname)s] - %(message)s")
        )

    logger.addHandler(stdout_handler)

    return logger
