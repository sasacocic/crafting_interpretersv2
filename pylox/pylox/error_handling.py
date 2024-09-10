from __future__ import annotations
import sys

from pylox.lox_scanner import Token, TokenType

had_error = False


def error_from_token(token: Token, message: str):
    if token.token_type == TokenType.EOF:
        report(token.line, " at end", message)
    else:
        report(token.line, " at '" + token.lexeme + "'", message)


def error(line: int, message: str) -> None:
    report(line, "", message)


def report(line: int, where: str, message: str) -> None:
    print(f"[line {line}] Error {where}: {message}")
    global had_error
    had_error = True


class LoxRuntimeError(Exception):
    token: Token

    def __init__(self, token: Token, msg: str, *args: object) -> None:
        super().__init__(msg)
        self.token = token


def runtime_error(error: LoxRuntimeError):
    msg, *rest = error.args
    print(msg + f"\n[line {error.token.line}]", file=sys.stderr)
    global had_error
    had_error = True


class ReturnException(Exception):
    value: object

    def __init__(self, value) -> None:
        # super().__init__(None, None, False, False)  # do I even need this?
        self.value = value
