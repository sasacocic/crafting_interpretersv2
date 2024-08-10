from __future__ import annotations
import py_jilox.scanner as scanner
import py_jilox.Expr as Expr
import py_jilox.error_handling as errors


class ParseError(Exception):
    pass


class Parser:
    tokens: list[scanner.Token]
    current: int

    def __init__(self, tokens: list[scanner.Token], current: int = 0) -> None:
        self.tokens = tokens
        self.current = current

    def parse(self) -> Expr.Expr | None:
        try:
            return self._expression()
        except ParseError:
            return None

    def _expression(self):
        return self._equality()

    # TODO: this is suppose to return a tree - there is a type for this. I should be returning that.
    def _equality(self):
        expr = self._comparison()

        while self.match(scanner.TokenType.BANG_EQUAL, scanner.TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self._comparison()
            expr = Expr.Binary(expr, operator, right)
        return expr

    def _comparison(self) -> Expr.Expr:
        expr = self._term()

        while self.match(
            scanner.TokenType.GREATER,
            scanner.TokenType.GREATER_EQUAL,
            scanner.TokenType.LESS,
            scanner.TokenType.LESS_EQUAL,
        ):
            operator = self.previous()
            right = self._term()
            expr = Expr.Binary(expr, operator, right)

        return expr

    def _term(self) -> Expr.Expr:
        expr = self._factor()

        while self.match(scanner.TokenType.MINUS, scanner.TokenType.PLUS):
            operator = self.previous()
            right = self._factor()
            expr = Expr.Binary(expr, operator, right)

        return expr

    def _factor(self):
        expr = self._unary()

        while self.match(scanner.TokenType.SLASH, scanner.TokenType.STAR):
            operator = self.previous()
            right = self._unary()
            expr = Expr.Binary(expr, operator, right)

        return expr

    def _unary(self):
        if self.match(scanner.TokenType.BANG, scanner.TokenType.MINUS):
            operator = self.previous()
            right = self._unary()
            return Expr.Unary(operator, right)

        return self._primary()

    def _primary(self):
        if self.match(scanner.TokenType.FALSE):
            return Expr.Literal("False")
        if self.match(scanner.TokenType.TRUE):
            return Expr.Literal("True")
        if self.match(scanner.TokenType.NIL):
            return Expr.Literal("Nil")

        if self.match(scanner.TokenType.NUMBER, scanner.TokenType.STRING):
            return Expr.Literal(
                self.previous().literal.__repr__()
            )  # literal should take object but I make it take string

        if self.match(scanner.TokenType.LEFT_PAREN):
            expr = self._expression()
            self._consume(scanner.TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Expr.Grouping(expr)

        raise self.error(self.peek(), "Expect expression.")

    def match(self, *token_types: scanner.TokenType) -> bool:
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def _consume(self, token_type: scanner.TokenType, message: str) -> scanner.Token:
        if self.check(token_type):
            self.advance()

        raise self.error(self.peek(), message)

    def error(self, token: scanner.Token, message: str) -> ParseError:
        # need to double check this
        errors.error_from_token(token, message)

        return ParseError()

    def synchronize(self):
        self.advance()

        while not self.is_at_end():
            if self.previous().token_type == scanner.TokenType.SEMICOLON:
                return

            match self.peek().token_type:
                case scanner.TokenType.CLASS:
                    return
                case scanner.TokenType.FUN:
                    return
                case scanner.TokenType.VAR:
                    return
                case scanner.TokenType.FOR:
                    return
                case scanner.TokenType.IF:
                    return
                case scanner.TokenType.WHILE:
                    return
                case scanner.TokenType.PRINT:
                    return
                case scanner.TokenType.RETURN:
                    return

            self.advance()

    def check(self, token_type: scanner.TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().token_type == token_type

    def advance(self):
        if not self.is_at_end():
            self.current += 1

        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().token_type == scanner.TokenType.EOF

    def peek(self) -> scanner.Token:
        return self.tokens[self.current]

    def previous(self) -> scanner.Token:
        return self.tokens[self.current - 1]
