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
            statements.append(self.declaration())
        return statements

    def declaration(self) -> stmnt.Stmnt | None:
        try:
            if self.match(TokenType.VAR):
                return self.var_declaration()
            return self.statement()
        except ParseError:
            self.synchronize()

    def var_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, "Expect variable name.")

        initializer: Expr.Expr | None = None

        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration")
        return stmnt.Var(name, initializer)

    def statement(self) -> stmnt.Stmnt:
        if self.match(TokenType.FOR):
            return self.for_statement()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.PRINT):
            return self.print_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.LEFT_BRACE):
            return stmnt.Block(self.block())

        return self.expression_statement()

    def for_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'")

        initializer = None
        if self.match(TokenType.SEMICOLON):
            pass
        elif self.match(TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition")

        increment = None

        if not self.check(TokenType.RIGHT_PAREN):
            increment = self.expression()

        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body = self.statement()
        if increment is not None:
            body = stmnt.Block([body, stmnt.Expression(increment)])

        if condition is None:
            condition = Expr.Literal(True)
        body = stmnt.While(condition, body)

        if initializer is not None:
            body = stmnt.Block([initializer, body])

        return body

    def while_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition")
        body = self.statement()

        return stmnt.While(condition, body)

    def if_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition")

        then_branch = self.statement()
        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.statement()

        return stmnt.If(condition, then_branch, else_branch)

    def block(self) -> list[stmnt.Stmnt]:
        statements = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def print_statement(self) -> stmnt.Stmnt:
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return stmnt.Print(value)

    def expression_statement(self) -> stmnt.Stmnt:
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return stmnt.Expression(expr)

    def expression(self):
        return self.assignment()

    def assignment(self):
        # expr = self.equality()
        expr = self.or_()

        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()

            if isinstance(expr, Expr.Variable):
                name = expr.name
                return Expr.Assign(name, value)

            errors.error_from_token(equals, "Invalid assignment target.")
        return expr

    def or_(self):
        expr = self.and_()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.and_()
            expr = Expr.Logical(expr, operator, right)

        return expr

    def and_(self):
        expr = self.equality()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.equality()
            expr = Expr.Logical(expr, operator, right)

        return expr

    # TODO: this is suppose to return a tree - there is a type for this. I should be returning that.
    def equality(self) -> Expr.Expr:
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

        return self.primary()

    def primary(self):
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

        if self.match(TokenType.IDENTIFIER):
            return Expr.Variable(self.previous())

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
