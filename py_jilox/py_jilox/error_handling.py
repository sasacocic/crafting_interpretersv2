from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    import py_jilox.scanner as scanner
had_error = False


def error_from_token(token: scanner.Token, message: str):
    # import py_jilox.scanner as scanner
    if token.token_type == scanner.TokenType.EOF:
        report(token.line, " at end", message)
    else:
        report(token.line, " at '" + token.lexeme + "'", message)


def error(line: int, message: str) -> None:
    report(line, "", message)


def report(line: int, where: str, message: str) -> None:
    print(f"[line {line}] Error {where}: {message}")
    global had_error
    had_error = True
