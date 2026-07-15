import logging


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO

    handlers = [logging.StreamHandler()]  # always log to terminal

    if not debug:
        handlers.append(logging.FileHandler("app.log"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )
