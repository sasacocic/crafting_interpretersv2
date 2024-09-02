from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    pass

import enum


class TokenType(enum.Enum):
    # Single-character tokens.
    LEFT_PAREN = 1
    RIGHT_PAREN = 2

    LEFT_BRACE = 3
    RIGHT_BRACE = 4
    COMMA = 5
    DOT = 6
    MINUS = 7
    PLUS = 8
    SEMICOLON = 9
    SLASH = 10
    STAR = 11

    # One or two character tokens.
    BANG = 12
    BANG_EQUAL = 13
    EQUAL = 14
    EQUAL_EQUAL = 15
    GREATER = 16
    GREATER_EQUAL = 17
    LESS = 18
    LESS_EQUAL = 19

    # Literals.
    IDENTIFIER = 20
    STRING = 21
    NUMBER = 22

    # Keywords.
    AND = 23
    CLASS = 24
    ELSE = 25
    FALSE = 26
    FUN = 27
    FOR = 28
    IF = 29
    NIL = 30
    OR = 31
    PRINT = 32
    RETURN = 33
    SUPER = 34
    THIS = 35
    TRUE = 36
    VAR = 37
    WHILE = 38

    EOF = 39


class Token:
    token_type: TokenType
    lexeme: str
    literal: typing.Any | None
    line: int

    def __init__(
        self, token_type: TokenType, lexeme: str, literal: dict | None, line: int
    ) -> None:
        self.token_type = token_type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __repr__(self) -> str:
        # TODO: need to look into enums in python more
        match self.literal:
            case str(literal):
                return str(self.token_type) + " " + self.lexeme + " " + literal
            case _:
                return str(self.token_type) + " " + self.lexeme
