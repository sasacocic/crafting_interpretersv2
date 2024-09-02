from __future__ import annotations
import sys
import typing
from pathlib import Path
import pylox.error_handling as errors
import pylox.lox_scanner as scan
import logging.config
import os
import pylox.Expr as Expr
import pylox.gen_exprs
import pylox.lox_parser as parser_mod
import click


if typing.TYPE_CHECKING:
    from pathlib import Path


LOG_LEVEL: typing.Final[str | None] = os.environ.get("LOG_LEVEL")

logging.config.dictConfig({
    "version": 1,
    "formatters": {"default": {"format": "[%(levelname)s][%(funcName)s] %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "loggers": {
        "pylox.scanner": {"level": LOG_LEVEL or logging.DEBUG},
        "pylox.lox_parser": {"level": LOG_LEVEL or logging.DEBUG},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL or logging.DEBUG},
})

LOGGER: typing.Final[logging.Logger] = logging.getLogger(__name__)


class Interpreter(Expr.Visitor[object]):
    def check_number_operand(self, operator: scan.Token, operand: object):
        if isinstance(operand, float):
            return
        raise errors.LoxRuntimeError(operator, "Operand must be a number.")

    def check_number_operands(self, operator: scan.Token, left: object, right: object):
        if isinstance(left, float) and isinstance(right, float):
            return

        raise errors.LoxRuntimeError(operator, "Operands must be numbers.")

    def visit_LiteralExpr(self, expr: Expr.Literal) -> object:
        LOGGER.info(f"Interpreting literal: {expr}")
        return expr.value

    def visit_GroupingExpr(self, expr: Expr.Grouping) -> object:
        return self.evaluate(expr.expression)

    def visit_UnaryExpr(self, expr: Expr.Unary) -> object:
        right = self.evaluate(expr.right)

        match expr.operator.token_type:
            case scan.TokenType.MINUS:
                self.check_number_operand(expr.operator, right)
                return -float(right)
            case scan.TokenType.BANG:
                return self.is_truthy(right)
            case _:
                return None  # unreachable?

    def visit_BinaryExpr(self, expr: Expr.Binary) -> object:
        LOGGER.info("evaluating BinaryExpression")
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        match expr.operator.token_type:
            case scan.TokenType.MINUS:
                self.check_number_operands(expr.operator, left, right)
                return float(left) - float(right)
            case scan.TokenType.SLASH:
                self.check_number_operands(expr.operator, left, right)
                return float(left) / float(right)
            case scan.TokenType.STAR:
                self.check_number_operands(expr.operator, left, right)
                return float(left) * float(right)
            case scan.TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return float(left) + float(right)
                if isinstance(left, str) and isinstance(right, str):
                    return (
                        str(left) + str(right)
                    )  # I don't need to technically do this they are already the correct type\
                raise errors.LoxRuntimeError(
                    expr.operator, "Operatnds must be two numbers or two strings"
                )
            case scan.TokenType.GREATER:
                self.check_number_operands(expr.operator, left, right)
                return float(left) > float(right)
            case scan.TokenType.GREATER_EQUAL:
                self.check_number_operands(expr.operator, left, right)
                return float(left) >= float(right)
            case scan.TokenType.LESS:
                self.check_number_operands(expr.operator, left, right)
                return float(left) < float(right)
            case scan.TokenType.LESS_EQUAL:
                self.check_number_operands(expr.operator, left, right)
                return float(left) <= float(right)
            case scan.TokenType.BANG_EQUAL:
                return not self.is_equal(left, right)
            case scan.TokenType.EQUAL_EQUAL:
                return self.is_equal(left, right)
            case _:
                return None  # should never happen

    def evaluate(self, expr: Expr.Expr):
        return expr.accept(self)

    def is_truthy(self, obj: object):
        if obj == None:
            return False
        if isinstance(obj, bool):
            return bool(obj)
        return True

    def is_equal(a: object, b: object) -> bool:
        if a == None and b == None:
            return True
        if a == None:
            return False

        return a == b

    def stringify(self, obj: object):
        if obj == None:
            return "nil"

        if isinstance(obj, float):
            text = str(obj)

            if text.endswith(".0"):
                text = int(float(text))
            return text

        return str(obj)

    def interpret(self, expression: Expr.Expr) -> None:
        try:
            value = self.evaluate(expression)
            print(self.stringify(value))
        except errors.LoxRuntimeError as e:
            errors.runtime_error(e)
            print("this is an error. I need to fix this message")


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

        return str(expr.value)

    def visit_UnaryExpr(self, expr: Expr.Unary):
        return self.parenthesize(expr.operator.lexeme, expr.right)

    def printer(self, expr: Expr.Expr):
        return expr.accept(self)


def run_prompt():
    # read evaluate print loop
    print("lox repl started! ")
    while True:
        sys.stdout.write("> ")
        sys.stdout.flush()
        line = sys.stdin.readline()
        if any((exit_word == line for exit_word in ["exit\n", "stop\n", "exit()\n"])):
            break
        result = run(line)
        print(">> ", result)
        errors.had_error = False


def run(lox_program: str) -> str:
    LOGGER.debug("running program: %s", lox_program)
    scanner = scan.Scanner(lox_program)
    tokens = scanner.scan_tokens()

    for token in tokens:
        print(
            f"token: {token}, [literal,type[literal]]: {(token.literal, type(token.literal))}"
        )
    LOGGER.debug("begin parsing")
    parser = parser_mod.Parser(tokens)
    expression = parser.parse()

    if errors.had_error or expression is None:
        return "there was some error"

    print("printer:", AstPrinter().printer(expression))
    print(f"evaluating: {type(expression).__name__}")
    Interpreter().interpret(expression)
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


@click.group()
def lox():
    pass


@click.command()
def repl():
    run_prompt()


@click.command()
@click.argument("lox_file")
def scanner(lox_file_path: str):
    lox_file = Path(lox_file_path)
    if not lox_file.exists():
        raise ValueError("file doesn't exist - this is the wrong error")
    run_file(lox_file)


@click.command()
def code_gen():
    LOGGER.debug("code_gen")
    pylox.gen_exprs.generate_ast()


@click.command()
def parser():
    LOGGER.debug("parser")


lox.add_command(scanner)
lox.add_command(parser)
lox.add_command(code_gen)
lox.add_command(repl)

if __name__ == "__main__":
    lox()
