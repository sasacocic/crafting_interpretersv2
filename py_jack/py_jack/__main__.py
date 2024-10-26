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
#        "py_jack.jack_scanner": {"level": logging.INFO},
#        "py_jack.jack_parser": {"level": LOG_LEVEL or logging.INFO},
        "py_jack.ast_nodes": {"level": LOG_LEVEL or logging.INFO},
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
        _tokens = scanner.scan()
        scanner.write_xml(path=output_file)
    else:
        raise FileNotFoundError(f"{file_path.resolve().name} not found")


def get_jack_files_in_path(path: pl.Path) -> list[pl.Path]:
    """
    returns all jack files at path

    if path is a directory returns all jack files in that directory
    if path is a single file it returns that single jack file
    otherwise it throws an error
    """
    if path.exists():
        files: list[pl.Path] = []
        if path.is_dir():
            for jack_file in path.glob("*.jack"):
                files.append(path / jack_file)
        else:
            files.append(path)
        files.sort()
        return files
    else:
        raise FileNotFoundError(f"{path.resolve().name} not found")


@click.command()
@click.argument("file-path")
def parser(file_path: str):
    """
    Reads a jack file and outputs a directory next to the file call 'parsed'. Inside that 
    that directory is XML files that represent the ASTs.
    """
    path = pl.Path(file_path)
    files = get_jack_files_in_path(path)
    for f in files:
        src_code = f.read_text()
        scanner = scan.Scanner(src_code)
        tokens = scanner.scan()
        parser = parse.Parser(tokens=tokens)
        class_node = parser.parse()
        p = f.parent / "parsed"
        p.mkdir(exist_ok=True)
        output = f.name.replace(".jack", "OUT.xml")
        class_node.write_xml(file=(p / output), indent=1)


@click.command()
@click.argument("file-path")
def compile(file_path: str):
    path = pl.Path(file_path)
    files = get_jack_files_in_path(path)
    for f in files:
        src_code = f.read_text()
        scanner = scan.Scanner(src_code)
        tokens = scanner.scan()
        parser = parse.Parser(tokens=tokens)
        class_node = parser.parse()
        vm_code_file_path = f.resolve()
        vm_code_file = vm_code_file_path.name.replace(".jack", ".vm")
        vm_file_path = vm_code_file_path.parent / vm_code_file
        class_node.compile(file=vm_file_path)


@click.command()
def repl():
    _repl()


if __name__ == "__main__":
    cli.add_command(scanner)
    cli.add_command(parser)
    cli.add_command(repl)
    cli.add_command(compile)
    cli()
