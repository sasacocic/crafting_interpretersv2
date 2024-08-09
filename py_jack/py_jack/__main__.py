from __future__ import annotations
import pathlib as pl
import py_jack.scanner as scan
import logging.config
import typing
import sys
import os


LOG_LEVEL: typing.Final[str | None] = os.environ.get("LOG_LEVEL")

logging.config.dictConfig({
    "version": 1,
    "formatters": {"default": {"format": "[%(levelname)s][%(funcName)s] %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "loggers": {"py_jack.scanner": {"level": LOG_LEVEL or logging.DEBUG}},
    "root": {"handlers": ["console"], "level": LOG_LEVEL or logging.DEBUG},
})

LOGGER: typing.Final[logging.Logger] = logging.getLogger(__name__)


"""
TODO: I need to double check how protocols work in python. Also, not really sure
what that I buying me here? It just seems like it's defining some attributes.
"""


def main():
    # TODO: read from argv to determine file name
    # jack_src = pl.Path("testing.jack")
    # jack_src = pl.Path("strings.jack")

    cur_path = pl.Path(".")
    LOGGER.info(f"root: {cur_path.resolve()}")
    command = sys.argv[1]
    match command:
        case "gen-exprs":
        case _:
            eval_file = command
            file_path = pl.Path(eval_file)
            if file_path.exists():
                src_code = file_path.read_text()
                scanner = scan.Scanner(src_code)
                tokens = scanner.scan()
                for token in tokens:
                    print(token)
            else:
                raise FileNotFoundError(f"{file_path.resolve().name} not found")


if __name__ == "__main__":
    main()
