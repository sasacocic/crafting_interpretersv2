from __future__ import annotations
import pylox.lox_scanner as lox_scanner
import pylox.Expr as Expr
import pylox.error_handling as errors
import logging

import pylox.Stmnt as stmnt
from pylox.tokens import TokenType


LOGGER = logging.getLogger(__name__)


class ParseError(Exception):
    pass


class Parser:
    tokens: list[lox_scanner.Token]
    current: int

    def __init__(self, tokens: list[lox_scanner.Token], current: int = 0) -> None:
        self.tokens = tokens
        self.current = current

    def parse(self) -> list[stmnt.Stmnt]:
        statements = []
        while not self.is_at_end():
            statements.append(self.statement())
        return statements

    def statement(self) -> stmnt.Stmnt:
        if self.match(TokenType.PRINT):
            return self.print_statement()

        return self.expression_statement()

    def print_statement(self) -> stmnt.Stmnt:
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return stmnt.Print(value)

    def expression_statement(self) -> stmnt.Stmnt:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return stmnt.Expression(expr)

    def expression(self):
        return self._equality()

    # TODO: this is suppose to return a tree - there is a type for this. I should be returning that.
    def _equality(self) -> Expr.Expr:
        expr = self._comparison()

        while self.match(
            lox_scanner.TokenType.BANG_EQUAL, lox_scanner.TokenType.EQUAL_EQUAL
        ):
            operator = self.previous()
            right = self._comparison()
            expr = Expr.Binary(expr, operator, right)
        return expr

    def _comparison(self) -> Expr.Expr:
        expr = self._term()

        while self.match(
            lox_scanner.TokenType.GREATER,
            lox_scanner.TokenType.GREATER_EQUAL,
            lox_scanner.TokenType.LESS,
            lox_scanner.TokenType.LESS_EQUAL,
        ):
            operator = self.previous()
            right = self._term()
            expr = Expr.Binary(expr, operator, right)

        return expr

    def _term(self) -> Expr.Expr:
        expr = self._factor()

        while self.match(lox_scanner.TokenType.MINUS, lox_scanner.TokenType.PLUS):
            operator = self.previous()
            right = self._factor()
            expr = Expr.Binary(expr, operator, right)

        return expr

    def _factor(self):
        expr = self._unary()

        while self.match(lox_scanner.TokenType.SLASH, lox_scanner.TokenType.STAR):
            operator = self.previous()
            right = self._unary()
            expr = Expr.Binary(expr, operator, right)

        return expr

    def _unary(self):
        if self.match(lox_scanner.TokenType.BANG, lox_scanner.TokenType.MINUS):
            operator = self.previous()
            right = self._unary()
            return Expr.Unary(operator, right)

        return self._primary()

    def _primary(self):
        if self.match(lox_scanner.TokenType.FALSE):
            return Expr.Literal(False)
        if self.match(lox_scanner.TokenType.TRUE):
            return Expr.Literal(True)
        if self.match(lox_scanner.TokenType.NIL):
            return Expr.Literal(None)

        if self.match(lox_scanner.TokenType.NUMBER, lox_scanner.TokenType.STRING):
            return Expr.Literal(
                self.previous().literal
            )  # literal should take object but I make it take string

        if self.match(lox_scanner.TokenType.LEFT_PAREN):
            expr = self.expression()
            LOGGER.debug(f"current: {self.peek()}")
            self.consume(
                lox_scanner.TokenType.RIGHT_PAREN, "Expect ')' after expression."
            )
            return Expr.Grouping(expr)

        raise self.error(self.peek(), "Expect expression.")

    def match(self, *token_types: lox_scanner.TokenType) -> bool:
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def consume(
        self, token_type: lox_scanner.TokenType, message: str
    ) -> lox_scanner.Token:
        if self.check(token_type):
            return self.advance()

        raise self.error(self.peek(), message)

    def error(self, token: lox_scanner.Token, message: str) -> ParseError:
        # need to double check this
        errors.error_from_token(token, message)

        return ParseError()

    def synchronize(self):
        self.advance()

        while not self.is_at_end():
            if self.previous().token_type == lox_scanner.TokenType.SEMICOLON:
                return

            match self.peek().token_type:
                case lox_scanner.TokenType.CLASS:
                    return
                case lox_scanner.TokenType.FUN:
                    return
                case lox_scanner.TokenType.VAR:
                    return
                case lox_scanner.TokenType.FOR:
                    return
                case lox_scanner.TokenType.IF:
                    return
                case lox_scanner.TokenType.WHILE:
                    return
                case lox_scanner.TokenType.PRINT:
                    return
                case lox_scanner.TokenType.RETURN:
                    return

            self.advance()

    def check(self, token_type: lox_scanner.TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().token_type == token_type

    def advance(self):
        if not self.is_at_end():
            self.current += 1

        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().token_type == lox_scanner.TokenType.EOF

    def peek(self) -> lox_scanner.Token:
        return self.tokens[self.current]

    def previous(self) -> lox_scanner.Token:
        return self.tokens[self.current - 1]
