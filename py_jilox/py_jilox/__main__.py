from __future__ import annotations
import sys
import typing
from pathlib import Path
import py_jilox.scanner as scan
import py_jilox.error_handling as errors
import logging.config
import os
import py_jilox.Expr as Expr
import py_jilox.gen_exprs as gen_exprs


if typing.TYPE_CHECKING:
    from pathlib import Path


LOG_LEVEL: typing.Final[str | None] = os.environ.get("LOG_LEVEL")

logging.config.dictConfig({
    "version": 1,
    "formatters": {"default": {"format": "[%(levelname)s][%(funcName)s] %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "loggers": {"py_jack.scanner": {"level": LOG_LEVEL or logging.DEBUG}},
    "root": {"handlers": ["console"], "level": LOG_LEVEL or logging.DEBUG},
})

LOGGER: typing.Final[logging.Logger] = logging.getLogger(__name__)


class AstPrinter(Expr.Visitor[str]):
    def to_string(self, expr: Expr.Expr):
        return expr.accept(self)

    def parenthesize(self, name: str, *exprs: Expr.Expr):
        builder = [f"({name}"]

        for expr in exprs:
            builder.append(" ")
            # TODO: look into this type error
            builder.append(expr.accept(self))

        builder.append(")")

        return "".join(builder)

    def visit_BinaryExpr(self, expr: Expr.Binary):
        return self.parenthesize(expr.operator.lexeme, expr.left, expr.right)

    def visit_GroupingExpr(self, expr: Expr.Grouping):
        return self.parenthesize("group", expr.expression)

    def visit_LiteralExpr(self, expr: Expr.Literal):
        if not expr.value:
            return "nil"

        return expr.value

    def visit_UnaryExpr(self, expr: Expr.Unary):
        return self.parenthesize(expr.operator.lexeme, expr.right)

    def printer(self, expr: Expr.Expr):
        return expr.accept(self)


def run_prompt():
    # read evaluate print loop
    while True:
        line = sys.stdin.readline()
        if "stop" in line:
            break
        result = run(line)
        print(result)
        errors.had_error = False


def run(lox_program: str) -> str:
    scanner = scan.Scanner(lox_program)
    tokens = scanner.scan_tokens()
    if errors.had_error:
        exit(65)  # no idea what 65 is

    for token in tokens:
        print(f"token: {token}")
    return ""


def run_file(path: Path):
    print(f"running the file: {path.resolve()}")

    # I believe read_text will read it in as utf-8
    run(path.read_text())


def test_ast_printer():
    # test the printer works as expected
    expression = Expr.Binary(
        Expr.Unary(
            scan.Token(scan.TokenType.MINUS, "-", None, 1),
            Expr.Literal("123"),
        ),
        scan.Token(scan.TokenType.STAR, "*", None, 1),
        Expr.Grouping(Expr.Literal("45.67")),
    )
    print(AstPrinter().printer(expression))


def main():
    print(f"argv: {sys.argv}")

    match len(sys.argv):
        case 1:
            print("no file passed. Aborting")
            exit(1)
        case 2:
            print(f"evaluating file: {sys.argv[1]}")
            lox_file = Path(sys.argv[1])
            if not lox_file.exists:
                raise ValueError("file doesn't exist - this is the wrong error")
            run_file(lox_file)
        case 3:
            if sys.argv[1] == "gen-attrs":
                gen_exprs.generate_ast()
            else:
                # TODO: remove this and function
                test_ast_printer()
        case _:
            run_prompt()


if __name__ == "__main__":
    main()
