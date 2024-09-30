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


@click.group()
def hack_vm():
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


def push_val(val: int):
    return f"""
    @{val} // value 
    D=A
    @0
    A=M
    M=D
    """ + increment_segment(0)


def increment_segment(segment: int):
    return f"""
    @{segment}
    M=M+1
    """


segments = {"constant": 0, "local": 1}


def decrement_segment(segment: int):
    return f"""
    @{segment}
    M=M-1    
    """


def pop_val(segment: int, index: int):
    # can only pop off the stack
    # return f"""
    # @0
    # D=M-1
    # A=D
    # D=M
    # @{segment}
    # A=M
    # M=D
    # """ + decrement_segment(0)  # decrement stack

    return f"""
    @{segment}
    D=M
    @{index}
    D=D+A
    @5
    M=D
    @0
    D=M-1
    A=D
    D=M
    @5
    A=M
    M=D
    """ + decrement_segment(0)  # decrement stack


def run(vm_commands: typing.TextIO):
    g = line_reader(vm_commands)
    output = ""
    for line in g:
        command, segment, index = line.split(" ")  # (\w)+ (\w)+ (\d)+
        match command:
            case "push":
                output += push_val(int(index))
            case "pop":
                output += pop_val(segments[segment], int(index))

    with open("output.asm", mode="w") as f:
        f.write(output)


hack_vm.add_command(translate)

if __name__ == "__main__":
    """
    RAM[0] - SP
    RAM[1] - LCL
    RAM[2] - ARG
    RAM[3] - THIS
    RAM[4] - THAT
    RAM[5:13] - TEMP 
    """
    hack_vm()
