import enum
import typing
import logging
import dataclasses

LOGGER: typing.Final[logging.Logger] = logging.getLogger(__name__)


class TokenType(enum.Enum):
    # symbols

    LEFT_CURLY = enum.auto()
    RIGHT_CURLY = enum.auto()
    LEFT_PAREN = enum.auto()
    RIGHT_PAREN = enum.auto()

    LEFT_SQUARE_BRACKET = enum.auto()
    RIGHT_SQUARE_BRACKET = enum.auto()

    DOT = enum.auto()
    COMMA = enum.auto()
    SEMICOLON = enum.auto()
    PLUS = enum.auto()
    MINUS = enum.auto()
    ASTERISK = enum.auto()
    FORWARD_SLASH = enum.auto()
    AMPERSAND = enum.auto()
    PIPE = enum.auto()
    LESS_THAN = enum.auto()
    GREATER_THAN = enum.auto()
    EQUAL = enum.auto()
    TILDE = enum.auto()

    # literals
    STRING_LITERAL = enum.auto()
    INTEGER_LITERAL = enum.auto()

    # keywords
    CLASS = enum.auto()
    CONSTRUCTOR = enum.auto()
    FUNCTION = enum.auto()
    METHOD = enum.auto()
    FIELD = enum.auto()
    STATIC = enum.auto()
    VAR = enum.auto()
    INT = enum.auto()
    CHAR = enum.auto()
    BOOLEAN = enum.auto()
    VOID = enum.auto()
    TRUE = enum.auto()
    FALSE = enum.auto()
    NULL = enum.auto()
    THIS = enum.auto()
    LET = enum.auto()
    DO = enum.auto()
    IF = enum.auto()
    ELSE = enum.auto()
    WHILE = enum.auto()
    RETURN = enum.auto()

    # identifier
    IDENTIFIER = enum.auto()


class Keywords(enum.StrEnum):
    CLASS = "class"
    CONSTRUCTOR = "constructor"
    FUNCTION = "function"
    METHOD = "method"
    FIELD = "field"
    STATIC = "static"
    VAR = "var"
    INT = "int"
    CHAR = "char"
    BOOLEAN = "boolean"
    VOID = "void"
    TRUE = "true"
    FALSE = "false"
    NULL = "null"
    THIS = "this"
    LET = "let"
    DO = "do"
    IF = "if"
    ELSE = "else"
    WHILE = "while"
    RETURN = "return"


@dataclasses.dataclass
class Token:
    token_type: TokenType
    lexeme: str
    start: int
    end: int


class Scanner:
    tokens: list[Token]
    src: str
    line: int
    start: int
    current: int

    keywords: typing.ClassVar[dict[str, TokenType]] = {
        Keywords.CLASS: TokenType.CLASS,
        Keywords.CONSTRUCTOR: TokenType.CONSTRUCTOR,
        Keywords.FUNCTION: TokenType.FUNCTION,
        Keywords.METHOD: TokenType.METHOD,
        Keywords.FIELD: TokenType.FIELD,
        Keywords.STATIC: TokenType.STATIC,
        Keywords.VAR: TokenType.VAR,
        Keywords.INT: TokenType.INT,
        Keywords.CHAR: TokenType.CHAR,
        Keywords.BOOLEAN: TokenType.BOOLEAN,
        Keywords.VOID: TokenType.VOID,
        Keywords.TRUE: TokenType.TRUE,
        Keywords.FALSE: TokenType.FALSE,
        Keywords.NULL: TokenType.NULL,
        Keywords.THIS: TokenType.THIS,
        Keywords.LET: TokenType.LET,
        Keywords.DO: TokenType.DO,
        Keywords.IF: TokenType.IF,
        Keywords.ELSE: TokenType.ELSE,
        Keywords.WHILE: TokenType.WHILE,
        Keywords.RETURN: TokenType.RETURN,
    }

    def __init__(self, src: str, tokens: list[Token] | None = None) -> None:
        self.src = src
        self.line = 1
        self.start = 0
        self.current = 0
        self.tokens = tokens or []

    def at_end(self):
        return self.current >= len(self.src)

    def advance(self):
        self.current += 1  # what about line and start?

    def scan(self) -> list[Token]:
        """
        read in source_prg and return a list of tokens
        """
        while not self.at_end():
            self.start = self.current
            self.scan_token()

        return self.tokens

    def add_token(self, token_type: TokenType, lexeme: str | None = None):
        lexeme = self.src[self.start : self.current + 1] if lexeme is None else lexeme
        # Note: end I don't think will always be right. I think I might need to pass that in.
        self.tokens.append(Token(token_type, lexeme, self.start, end=self.current))

    def scan_token(self):
        c = self.src[self.current]

        LOGGER.debug(f"src[current]: {c}")
        match c:
            case "{":
                self.add_token(TokenType.LEFT_CURLY)
            case "}":
                self.add_token(TokenType.RIGHT_CURLY)
            case "(":
                self.add_token(TokenType.LEFT_PAREN)
            case ")":
                self.add_token(TokenType.RIGHT_PAREN)
            case "[":
                self.add_token(TokenType.LEFT_SQUARE_BRACKET)
            case "]":
                self.add_token(TokenType.RIGHT_SQUARE_BRACKET)
            case ".":
                self.add_token(TokenType.DOT)
            case ",":
                self.add_token(TokenType.COMMA)
            case ";":
                self.add_token(TokenType.SEMICOLON)
            case "=":
                self.add_token(TokenType.EQUAL)
            case "-":
                self.add_token(TokenType.MINUS)
            case "*":
                self.add_token(TokenType.ASTERISK)
            case "/":
                LOGGER.debug("comment or division")
                if not self.at_end() and self.peek() == "/":
                    LOGGER.debug("Found comment")
                    while self.peek() != "\n":
                        if self.at_end():
                            break
                        self.advance()  # we found a comment
                        if not self.at_end():
                            LOGGER.debug(
                                f"now at({self.current}): {self.src[self.current]}"
                            )
                else:
                    LOGGER.debug("Found division")
                    self.add_token(TokenType.FORWARD_SLASH)
            case "&":
                self.add_token(TokenType.AMPERSAND)
            case "|":
                self.add_token(TokenType.PIPE)
            case "<":
                self.add_token(TokenType.LESS_THAN)
            case ">":
                self.add_token(TokenType.GREATER_THAN)
            case "=":
                self.add_token(TokenType.EQUAL)
            case "~":
                self.add_token(TokenType.TILDE)
            case '"':
                self.string()
            case "" | " ":
                pass
            case "\n":
                self.line += 1
            case _:
                # pretty sure this is a problem. would parse some thing like 1234hello as an identifier - which actually maybe ok?
                if c.isdigit():
                    # looking at a integer constant
                    self.integer_constant(c)
                elif c.isalpha():
                    # we must be looking at an identifier or keyword?
                    # maximal munch - that means the longer of the two is what the thing becomes
                    self.ident_or_keyword()
                else:
                    raise Exception("unknown lexeme - breaking out of thing")
        self.advance()

    def can_peek(self):
        return (self.current + 1) <= len(self.src) - 1

    def peek(self):
        if (self.current + 1) <= len(self.src) - 1:
            return self.src[self.current + 1]

    def string(self):
        while self.peek() != '"':
            self.advance()
        else:
            self.advance()  # want current to be equal to "

        text = self.src[
            self.start : self.current + 1
        ]  # +1 because I want the ending quote right?
        self.add_token(TokenType.STRING_LITERAL, lexeme=text)

    def ident_or_keyword(self):
        """
        parses the string and determines if it's an identifier or keyword
        """
        cur = self.peek()
        while cur.isalnum() and self.can_peek():
            self.advance()
            cur = self.peek()

        lexeme = self.src[self.start : self.current + 1]
        LOGGER.debug(f"lexeme: '{lexeme}'")
        if lexeme in self.keywords:
            self.add_token(self.keywords[lexeme], lexeme=lexeme)
        else:
            self.add_token(TokenType.IDENTIFIER, lexeme=lexeme)

    def keyword(self, lexem):
        raise NotImplementedError()

    def identifier(self):
        raise NotImplementedError()

    def integer_constant(self, c: str):
        while (c := self.peek()) and c.isdigit():
            self.advance()
        # parses digit and creates digit token
        lexeme = self.src[self.start : self.current + 1]
        self.add_token(TokenType.INTEGER_LITERAL, lexeme)
