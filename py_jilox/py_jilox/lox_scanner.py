from __future__ import annotations
import typing
import py_jilox.error_handling as errors

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


class Scanner:
    source: str
    tokens: list[Token]
    start: int  # do these default values make these class level or instance level? | start points to the first char in the lexeme
    current: int  # points to the current char in the lexeme being considered
    line: int  # points to the line of the current lexeme being considered
    """
    example: 
        var <- lexeme being considered
        ^^
        (v) - would be start
        (a) - would be current. After a then r would be considered. That would be current + 1
    """

    keywords: typing.ClassVar[dict[str, TokenType]] = {
        "AND": TokenType.AND,
        "CLASS": TokenType.CLASS,
        "ELSE": TokenType.ELSE,
        "FALSE": TokenType.FALSE,
        "FUN": TokenType.FUN,
        "FOR": TokenType.FOR,
        "IF": TokenType.IF,
        "NIL": TokenType.NIL,
        "OR": TokenType.OR,
        "PRINT": TokenType.PRINT,
        "RETURN": TokenType.RETURN,
        "SUPER": TokenType.SUPER,
        "THIS": TokenType.THIS,
        "TRUE": TokenType.TRUE,
        "VAR": TokenType.VAR,
        "WHILE": TokenType.WHILE,
    }

    def __init__(self, source: str) -> None:
        self.source = source
        self.start = 0
        self.current = 0
        self.line = 0
        self.tokens = []

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self):
        next_char = self.source[self.current]
        self.current += 1
        return next_char

    def add_token(self, token_type: TokenType, literal: typing.Any | None = None):
        text = self.source[self.start : self.current]  # current won't be included...
        self.tokens.append(
            Token(token_type=token_type, lexeme=text, literal=literal, line=self.line)
        )

    def match(self, expected: str):
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False

        self.current += 1
        return True

    def peek(self) -> str:
        if self.is_at_end():
            return "\0"
        return self.source[self.current]

    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def scan_token(self):
        c = self.advance()
        match c:
            # TODO: rest of the lexemes
            case "(":
                self.add_token(TokenType.LEFT_PAREN)
            case ")":
                self.add_token(TokenType.RIGHT_PAREN)
            case "{":
                self.add_token(TokenType.LEFT_BRACE)
            case "}":
                self.add_token(TokenType.RIGHT_BRACE)
            case ",":
                self.add_token(TokenType.COMMA)
            case ".":
                self.add_token(TokenType.DOT)
            case "-":
                self.add_token(TokenType.MINUS)
            case "+":
                self.add_token(TokenType.PLUS)
            case ";":
                self.add_token(TokenType.SEMICOLON)
            case "*":
                self.add_token(TokenType.STAR)
            case "!":
                self.add_token(
                    TokenType.BANG_EQUAL if self.match("=") else TokenType.STAR
                )
            case "=":
                self.add_token(
                    TokenType.EQUAL_EQUAL if self.match("=") else TokenType.EQUAL
                )
            case "<":
                self.add_token(
                    TokenType.LESS_EQUAL if self.match("=") else TokenType.LESS
                )
            case ">":
                self.add_token(
                    TokenType.GREATER_EQUAL if self.match("=") else TokenType.GREATER
                )
            case "/":
                if self.match("/"):
                    while self.peek() != "\n" and not self.is_at_end():
                        self.advance()
                else:
                    self.add_token(TokenType.SLASH)
            case " " | "\r" | "\t":
                pass
            case "\n":
                self.line += 1
            case '"':
                self.string()
            case _:
                if self.is_digit(c):
                    self.number()
                elif self.is_alpha(c):
                    self.identifier()
                else:
                    errors.error(self.line, "Unexpected character.")

    def identifier(self):
        while self.is_alpha_numeric(self.peek()):
            self.advance()

        text = self.source[self.start : self.current]
        token_type = self.keywords.get(text)
        if not token_type:
            token_type = TokenType.IDENTIFIER

        self.add_token(token_type)

    def is_alpha(self, c: str):
        cc = ord(c)
        return (
            (cc >= ord("a") and cc <= ord("z"))
            or (cc >= ord("A") and cc <= ord("Z"))
            or c == "_"
        )

    def is_alpha_numeric(self, c: str):
        return self.is_alpha(c) or self.is_digit(c)

    def number(self):
        while self.is_digit(self.peek()):
            self.advance()

        if self.peek() == "." and self.is_digit(self.peek_next()):
            self.advance()
            while self.is_digit(self.peek()):
                self.advance()

        self.add_token(
            TokenType.NUMBER, float(self.source[self.start : self.current])
        )  # TODO: I feel like self.current + 1 is what is actually needed here

    def is_digit(self, c: str):
        return ord(c) >= ord("0") and ord(c) <= ord("9")

    def string(self):
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == "\n":
                self.line += 1
            self.advance()

        if self.is_at_end():
            errors.error(self.line, "Unterminated string.")
            return None

        self.advance()

        value = self.source[self.start + 1 : self.current - 1]
        self.add_token(TokenType.STRING, value)

    def scan_tokens(self) -> list[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens
