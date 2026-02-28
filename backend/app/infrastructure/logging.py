import logging


def init_logger() -> None:
    logging.getLogger("uvicorn.access").addFilter(lambda r: "GET /health" not in r.getMessage())
