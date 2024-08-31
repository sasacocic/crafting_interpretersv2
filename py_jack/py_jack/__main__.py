from __future__ import annotations
import pathlib as pl
import py_jack.jack_scanner as scan
import py_jack.jack_parser as parse
import logging.config
import typing
import sys
import os
import click
import pathlib


LOG_LEVEL: typing.Final[str | None] = os.environ.get("LOG_LEVEL")

logging.config.dictConfig({
    "version": 1,
    "formatters": {
        "default": {"format": "[%(levelname)s][%(funcName)s:%(lineno)d] %(message)s"}
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "loggers": {
        "py_jack.scanner": {"level": LOG_LEVEL or logging.INFO},
        "py_jack.parser": {"level": LOG_LEVEL or logging.INFO},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL or logging.INFO},
})

LOGGER: typing.Final[logging.Logger] = logging.getLogger(__name__)


def _repl():
    """
    starts a repl and executes code.
    """
    # TODO: catch ctrl-c signal
    print("py_jack repl has started! type 'exit' to exit the repl")
    while True:
        code = sys.stdin.readline()
        if code.strip() == "exit":
            break
        # TODO: could put this in a try catch
        scanner = scan.Scanner(code)
        scanner.scan()
        LOGGER.debug("scanning complete. Spitting out tokens.")
        for token in scanner.tokens:
            LOGGER.debug(token)
        LOGGER.debug("----------------------- TOKEN END -----------------------")
        LOGGER.debug("parser")
        parser = parse.Parser(scanner.tokens)
        parse_result = parser.parse()

        xml_file = pathlib.Path("output.xml")
        parse_result.write_xml(xml_file, 1)
    print("Exiting. Thanks for using the repl!")


@click.group()
def cli():
    pass


@click.command()
@click.argument("file-path")
@click.option("--output-file", default="output.xml", help="name of the file to output")
def scanner(file_path, output_file):
    file_path = pl.Path(file_path)
    if file_path.exists():
        src_code = file_path.read_text()
        scanner = scan.Scanner(src_code)
        tokens = scanner.scan()
        for token in tokens:
            print(token)
        scanner.write_xml(path=output_file)
    else:
        raise FileNotFoundError(f"{file_path.resolve().name} not found")


def get_jack_and_xml_files(directory: pl.Path) -> list[pl.Path]:
    files: list[pl.Path] = []
    for jack_file in directory.glob("*.jack"):
        files.append(directory / jack_file)

    return files


@click.command()
@click.argument("file-path")
@click.option("--output-file", default="output.xml", help="name of the file to output")
def parser(file_path: str, output_file: str):
    path = pl.Path(file_path)
    if path.exists():
        files: list[pl.Path] = []
        if path.is_dir():
            files.extend(get_jack_and_xml_files(path))
        else:
            files.append(path)
        for f in files:
            src_code = f.read_text()
            scanner = scan.Scanner(src_code)
            tokens = scanner.scan()
            parser = parse.Parser(tokens=tokens)
            class_node = parser.parse()
            p = f.parent / "parsed"
            p.mkdir(exist_ok=True)
            output = f.name.replace(".jack", "OUT.xml")
            class_node.write_xml(file_path=(p / output), indent=1)
    else:
        raise FileNotFoundError(f"{file_path.resolve().name} not found")


@click.command()
def repl():
    _repl()


if __name__ == "__main__":
    cli.add_command(scanner)
    cli.add_command(parser)
    cli.add_command(repl)
    cli()
