"""
In a nutshell this program needs to take in vm commands

stack commands
- push segment i
- pop segment i

arithmetic and logical commands
- add
- sub
- neg
- eq
- gt
- lt
- and
- or
- not
"""

import typing
import click
import pathlib
import hack_vm
import re
import logging.config


logging.config.dictConfig({
    "version": 1,
    "formatters": {"default": {"format": "[%(levelname)s]:%(msg)s"}},
    "handlers": {
        "default": {"class": "logging.StreamHandler", "formatter": "default"},
    },
    "root": {"handlers": ["default"], "level": logging.DEBUG},
})


LOGGER: typing.Final = logging.getLogger(__name__)


segments = {
    "constant": 0,
    "local": 1,
    "argument": 2,
    "this": 3,
    "that": 4,
    "temp": 5,
    "pointer": 6,
    "static": 7,
}


@click.group()
def hack_vm_cli():
    pass


@click.command()
@click.argument("vm_code")
@click.option(
    "--no-bootstrap", is_flag=True, help="exclude bootstrap code", default=False
)
def translate(vm_code: str, no_bootstrap: bool):
    LOGGER.info("bootstrap: %s" % no_bootstrap)
    src_file = pathlib.Path(vm_code)
    if not src_file.exists():
        raise FileNotFoundError(f"{src_file} - does not exist")

    files: list[pathlib.Path] = []
    if src_file.is_dir():
        for f in src_file.glob("*.vm"):
            files.append(f)
    else:
        files.append(src_file)

    run(files, src_file.name[: len(src_file.name) - 3] + ".asm", no_bootstrap)


def line_reader(vm_commands: typing.TextIO):
    # how this is getting EOF is really unclear, but
    # it seems to work
    while line := vm_commands.readline():
        yield line


def run(files: list[pathlib.Path], output_file: str, no_bootstrap: bool):
    """
    How I would like this to work
    1. get a list of filenames
        - for each file name read it and write it to a file
    """
    # vm_commands: typing.TextIO,

    # I think bootstrap will break everything else...
    bootstrap = """
    @256
    D=A
    @SP
    M=D
    """ + hack_vm.ops.call("Sys.init", 0)

    if no_bootstrap:
        with open(output_file, mode="w") as f:
            LOGGER.info("wrote bootstrap to: %s" % output_file)
            f.write("")
    else:
        with open(output_file, mode="w") as f:
            LOGGER.info("wrote bootstrap to: %s" % output_file)
            f.write(bootstrap)

    for file_path in files:
        with file_path.open() as f:
            file_name = file_path.name[: len(file_path.name) - 3]
            g = line_reader(f)

            output = ""
            for line in g:
                split = line.split(" ")
                match_line = split[0].strip()
                if match_line.startswith("//") or match_line == "":
                    continue
                # I thought regex would help, but having a hard time extracting
                # the tokens I want
                # print(f"line: {line}")
                # split = re.findall(r"^push \w+ \d+|^pop \w+ \d+|add", line)
                # print(f"split: {split}")
                match match_line:
                    case "push":
                        segment, index = (
                            split[1].strip(),
                            "".join([c for c in split[2] if re.match(r"\d", c)]),
                        )
                        output += hack_vm.ops.push_val(
                            segments[segment], int(index), file_name
                        )
                    case "pop":
                        segment, index = split[1], split[2]
                        output += hack_vm.ops.pop_val(
                            segments[segment], int(index), file_name
                        )
                    case "add":
                        # pop off the top two things of the stack and then push
                        # them onto the stack
                        output += hack_vm.ops.add()
                    case "sub":
                        output += hack_vm.ops.sub()
                    case "eq":
                        output += hack_vm.ops.eq()
                    case "lt":
                        output += hack_vm.ops.lt()
                    case "gt":
                        output += hack_vm.ops.gt()
                    case "neg":
                        output += hack_vm.ops.neg()
                    case "and":
                        output += hack_vm.ops.and_()
                    case "or":
                        output += hack_vm.ops.or_()
                    case "not":
                        output += hack_vm.ops.not_()
                    case "label":
                        label = split[1].strip()
                        output += hack_vm.ops.label(label)
                    case "goto":
                        label = split[1].strip()
                        output += hack_vm.ops.goto(label)
                    case "if-goto":
                        label = split[1].strip()
                        output += hack_vm.ops.if_goto(label)
                    case "function":
                        function_name, n_args = split[1], split[2]
                        output += hack_vm.ops.function(function_name, int(n_args))
                    case "call":
                        function_name, n_args = split[1], split[2]
                        output += hack_vm.ops.call(function_name, int(n_args))
                    case "return":
                        output += hack_vm.ops.return_()
                    case _:
                        raise Exception(
                            f"Unknown command: '{split[0].strip()}'. This should never happen"
                        )

            with open(output_file, mode="a") as f:
                LOGGER.info("wrote %s to %s" % (file_path.name, output_file))
                f.write(output)


hack_vm_cli.add_command(translate)

if __name__ == "__main__":
    """
    RAM[0] - SP
    RAM[1] - LCL
    RAM[2] - ARG
    RAM[3] - THIS
    RAM[4] - THAT
    RAM[5:13] - TEMP 
    """
    LOGGER.debug("program starting")
    hack_vm_cli()
