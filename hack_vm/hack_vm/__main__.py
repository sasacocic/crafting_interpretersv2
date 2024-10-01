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


@click.group()
def hack_vm_cli():
    pass


@click.command()
@click.argument("vm_code")
def translate(vm_code: str):
    src_file = pathlib.Path(vm_code)
    if not src_file.exists():
        raise FileNotFoundError(f"{src_file} - does not exist")

    with src_file.open() as f:
        run(f)


def line_reader(vm_commands: typing.TextIO):
    # how this is getting EOF is really unclear, but
    # it seems to work
    while line := vm_commands.readline():
        yield line


segments = {"constant": 0, "local": 1, "argument": 2, "this": 3, "that": 4, "temp": 5}


def run(vm_commands: typing.TextIO):
    g = line_reader(vm_commands)
    output = ""
    for line in g:
        split = line.split(" ")
        # I thought regex would help, but having a hard time extracting
        # the tokens I want
        # print(f"line: {line}")
        # split = re.findall(r"^push \w+ \d+|^pop \w+ \d+|add", line)
        # print(f"split: {split}")
        match split[0].strip():
            case "push":
                segment, index = split[1], split[2]
                output += hack_vm.ops.push_val(segments[segment], int(index))
            case "pop":
                segment, index = split[1], split[2]
                output += hack_vm.ops.pop_val(segments[segment], int(index))
            case "add":
                # pop off the top two things of the stack and then push
                # them onto the stack
                output += hack_vm.ops.add()
            case "sub":
                output += hack_vm.ops.sub()
            case _:
                print(split[0].strip())
                raise Exception("Unknown command. This should never happen")

    with open("output.asm", mode="w") as f:
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
    hack_vm_cli()
