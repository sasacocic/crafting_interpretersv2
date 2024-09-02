"""
This is simply a script used for generating classes in the Expr.py file.
"""

from __future__ import annotations
import typing
from pathlib import Path
import logging.config
import io

LOGGER: typing.Final[logging.Logger] = logging.getLogger(__name__)


def define_type(f: io.TextIOWrapper, base_name: str, class_name: str, fields: str):
    f.write(f"class {class_name}({base_name}):\n")
    f.write(f"   def __init__(self, {fields}):\n")

    for name_type in fields.split(","):
        print(f"name_type: '{name_type}'")
        name = name_type.strip().split(" ")[0][:-1]
        print(f"name: '{name}'")
        f.write(f"      self.{name} = {name}\n")

    f.write("   def accept[T](self, visitor: Visitor[T]):\n")
    f.write(f"      return {"visitor.visit" + "_" + class_name + base_name}(self)\n")


def define_visitor(f: io.TextIOWrapper, base_name: str, types: list[str]):
    f.write("class Visitor[T]:\n")

    for typee in types:
        type_name = typee.split("|")[0].strip()

        f.write(
            f"   def visit_{type_name + base_name}(self, {base_name.lower()}:{type_name}) -> T:...\n\n"
        )
        # f.write(f"   def visit_{type_name + base_name}(self, {type_name.lower()}:{type_name}):\n")


def define_ast(output_dir: Path, base_name: str, types: list[str]):
    LOGGER.debug("writing exprs to: {output_dir}")
    output_path = Path(output_dir)
    if not output_path.exists():
        print(f"{output_dir} does not exist. Aborting.")
        exit(99)

    write_path = None
    base_name = "Expr"
    if output_path.is_dir():
        write_path = output_path / (base_name + ".py")
    else:
        # must be a file right?
        write_path = output_path

    with write_path.open(mode="+w") as f:
        lines = [
            "from __future__ import annotations\n",
            "from py_jilox.scanner import Token\n",
            "import typing\n",
            f"class {base_name}(typing.Protocol):\n",
            "   def accept[T](self, visitor: Visitor[T]) -> T:...\n\n",
        ]

        f.writelines(lines)

        define_visitor(f, base_name, types)
        for typee in types:
            class_name, fields = typee.split("|")
            class_name = class_name.strip()
            fields = fields.strip()
            define_type(f, base_name, class_name, fields)


def generate_ast():
    output_dir = "py_jilox"

    define_ast(
        Path(output_dir),
        "Expr",
        types=[
            "Binary | left: Expr , operator: Token , right: Expr",
            "Grouping | expression: Expr",
            "Literal | value: object",
            "Unary | operator: Token, right: Expr",
        ],
    )

    # wtf is the implication if this is a directory? I can't write to a directory can I? Does this
    # need to be a file or
