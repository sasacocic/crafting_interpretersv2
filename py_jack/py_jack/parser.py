from __future__ import annotations
from collections.abc import Iterator
import py_jack.scanner as scanner
import logging
import itertools
import functools
import py_jack.ast

LOGGER = logging.getLogger(__name__)


class Parser:
    """
    recursive descent parser
    """

    tokens: list[scanner.Token]
    token_iter: Iterator[scanner.Token]

    def __init__(self, tokens: list[scanner.Token]) -> None:
        LOGGER.debug("begin parsing with tokens: %s", tokens)
        self.tokens = tokens
        self.token_iter = iter(self.tokens)

    def _next(self):
        LOGGER.debug("_next called")
        val = next(self.token_iter)
        LOGGER.debug("next token: %s", val)
        return val

    def _peek(self):
        """
        really dumb solution that just clones and then returns top of the iterator
        """

        top = next(self.token_iter, None)
        if top is None:
            return top
        new_iter = itertools.chain([top], self.token_iter)
        self.token_iter = new_iter
        return top

    def _peek_token_type(self):
        top = self._peek()
        return top.token_type if top else None

    def parse(self):
        return self.parse_class()

    def parse_class(self) -> py_jack.ast.ClassNode:
        token = self._next()
        match token.lexeme:
            case "class":
                class_name = self.parse_class_name()
                left_squerly = self._next()
                class_var_dec = None
                if self._peek().lexeme in ["static", "field"]:
                    class_var_dec = (
                        self.parse_class_var_dec()
                    )  # this is potentially empty
                subroutine_dec = self.parse_subroutine_dec()
                right_squerly = self._next()
                return py_jack.ast.ClassNode(
                    class_name=class_name, class_var_dec=[class_var_dec]
                )
            case _:
                raise Exception("didn't start with class keyword")

    def parse_class_name(self):
        class_name = self._next()
        if class_name.token_type != scanner.TokenType.IDENTIFIER:
            raise Exception(f"{class_name} not an identifier")
        return class_name

    def parse_class_var_dec(self) -> py_jack.ast.ClassVarDec:
        field_type = self._next()
        if not any([
            field_type.lexeme == valid_lexeme for valid_lexeme in ["static", "field"]
        ]):
            raise Exception(
                f"{field_type} - not valid. Needs to be 'static' or 'field'"
            )

        type_ = self.parse_type()
        varname = self.parse_varname()
        semi_colon = self._next()
        if semi_colon.lexeme != ";":
            raise Exception(f"expected ';', but found {semi_colon}")

        cvd = py_jack.ast.ClassVarDec(
            field_type=field_type, type_=type_, var_name=[varname]
        )
        print(f"cvd: {cvd}")
        return cvd

    def parse_subroutine_dec(self):
        dec_type = self._next()
        routine_name = self._next()

        left_paren = self._next()
        parameter_list = self.parse_parameter_list()
        right_paren = self._next()

        routine_body = self.parse_subroutine_body()

        return ""  # TODO: actually need to finish this

    def parse_parameter_list(self) -> py_jack.ast.ParameterList:
        type_var_name = []

        # TODO: why am I not using parse type here????
        while self._peek() and self._peek().token_type in scanner.type_tokens:
            type_ = self._next()
            var_name = self._next()
            assert var_name.token_type == scanner.TokenType.IDENTIFIER
            type_var_name.append((type_, var_name))
            if self._peek() and self._peek().token_type == scanner.TokenType.COMMA:
                self._next()
        else:
            LOGGER.debug("parameter_list ending with: %s", self._peek())

        return py_jack.ast.ParameterList(parameters=type_var_name)

    def parse_subroutine_body(self):
        left_squerly = self._next()
        # TODO: implement statements - for now why not just implement one statement?

    def parse_type(self):
        token = self._next()

        if not any([
            token.token_type == valid_token_type
            for valid_token_type in [
                scanner.TokenType.INT,
                scanner.TokenType.CHAR,
                scanner.TokenType.BOOLEAN,
                scanner.TokenType.IDENTIFIER,
            ]
        ]):
            raise Exception(f"{token} - not valid. Needs to be 'static' or 'field'")

        return token

    def parse_varname(self) -> scanner.Token:
        token = self._next()

        if token.token_type != scanner.TokenType.IDENTIFIER:
            raise Exception(f"{token} - not valid. Needs to be an identifier")

        return token

    # statment parsing

    def parse_constant(self):
        constant = self._next()
        assert constant.token_type in scanner.literals
        return constant

    def parse_statements(self):
        statements: list[py_jack.ast.Statement] = []
        top = self._peek_token_type()
        print(f"top: {top.name} - {top in scanner.statements}")
        while self._peek_token_type() in scanner.statements:
            statements.append(self.statement())
        return statements

    def statement(self) -> py_jack.ast.Statement:
        statement = None
        match self._peek_token_type():
            case scanner.TokenType.LET:
                statement = self.let_statement()
            case scanner.TokenType.IF:
                statement = self.if_statement()
            case scanner.TokenType.WHILE:
                statement = self.while_statement()
            case scanner.TokenType.DO:
                statement = self.do_statement()
            case scanner.TokenType.RETURN:
                statement = self.return_statement()
            case _:
                raise Exception("statment didn't match one of the statements")

        return statement

    def if_statement(self):
        if_kw = self._next()
        l_paren = self._next()
        expression = self.expression()
        r_paren = self._next()
        l_curly = self._next()
        statements = self.parse_statements()
        r_curly = self._next()
        if_statement = py_jack.ast.IfStatement(
            if_kw=if_kw,
            left_paren=l_paren,
            expression=expression,
            right_paren=r_paren,
            left_curly=l_curly,
            statements=statements,
            right_curly=r_curly,
        )

        if (else_kw := self._peek_token_type()) and else_kw == scanner.TokenType.ELSE:
            else_kw = self._next()
            else_left_curly = self._next()
            else_statements = self.parse_statements()
            else_right_curly = self._next()
            if_statement.optional_else = (
                else_kw,
                else_left_curly,
                else_statements,
                else_right_curly,
            )
        return if_statement

    def while_statement(self):
        while_kw = self._next()
        l_paren = self._next()
        expression = self.expression()
        r_paren = self._next()
        l_curly = self._next()
        statements = self.parse_statements()
        r_curly = self._next()
        return py_jack.ast.WhileStatement(
            while_kw=while_kw,
            left_paren=l_paren,
            expression=expression,
            right_paren=r_paren,
            left_curly=l_curly,
            statements=statements,
            right_curly=r_curly,
        )

    def return_statement(self):
        return_kw = self._next()
        if return_kw.token_type != scanner.TokenType.RETURN:
            raise Exception("expected return keyword - didn't get it")

        expression = (
            self.expression()
        )  # this is optional - need to come back and fix this
        semi_colon = self._next()
        return py_jack.ast.ReturnStatement(
            return_kw=return_kw, expression=expression, semicolon=semi_colon
        )

    def do_statement(self):
        do_kw = self._next()
        if do_kw.token_type != scanner.TokenType.DO and do_kw.lexeme != "do":
            raise Exception("expected do keyword - didn't get it")

        subroutine_ident = self._next()
        subroutine = self.subroutine_call(sub_name=subroutine_ident)
        semi_colon = self._next()
        return py_jack.ast.DoStatement(
            do_kw=do_kw, subroutine_call=subroutine, semicolon=semi_colon
        )

    def let_statement(self):
        LOGGER.info("parsing:let_statement")
        let_kw = self._next()
        if let_kw.token_type != scanner.TokenType.DO and let_kw.lexeme != "let":
            raise Exception("expected let keyword - didn't get it")

        ident = self._next()
        match self._peek().token_type:
            case scanner.TokenType.LEFT_SQUARE_BRACKET:
                left_square = self._next()
                optional_expr = self.expression()
                right_square = self._next()
                equal = self._next()
                expr = self.expression()
                semi_colon = self._next()

                return py_jack.ast.LetStatement(
                    let_kw=let_kw,
                    var_name=ident,
                    equal=equal,
                    expression=expr,
                    semi_colon=semi_colon,
                    index_var=(left_square, optional_expr, right_square),
                )
            case _:
                equal = self._next()
                expr = self.expression()
                semi_colon = self._next()
                return py_jack.ast.LetStatement(
                    let_kw=let_kw,
                    var_name=ident,
                    equal=equal,
                    expression=expr,
                    semi_colon=semi_colon,
                )

    # expression parsing
    def expression(self):
        LOGGER.debug(f"expression:tokens: {self.tokens}")
        term = self.term()
        ops_and_terms = []
        while (top := self._peek()) and top.token_type in scanner.operations:
            LOGGER.debug("looking at (op term)*")
            ops_and_terms.append((self.op(), self.term()))
        return py_jack.ast.Expression(term=term, op_terms=ops_and_terms)

    def term(self) -> py_jack.ast.Term:
        LOGGER.debug(f"term:tokens: {self.tokens}")
        top = self._peek()
        matcher = top.token_type if top else None
        match matcher:
            case scanner.TokenType.STRING_CONSTANT:
                return py_jack.ast.Term(term=self.string_constant())
            case scanner.TokenType.INTEGER_CONSTANT:
                return py_jack.ast.Term(term=self.integer_constant())
            case token if token in scanner.keyword_constants:
                return py_jack.ast.Term(term=self.keyword_constant())
            case scanner.TokenType.LEFT_PAREN:
                left_paren = self._next()
                expression = self.expression()
                right_paren = self._next()
                if right_paren.token_type != scanner.TokenType.RIGHT_PAREN:
                    raise Exception("expected right paren - didn't recieve")
                return py_jack.ast.Term(term=(left_paren, expression, right_paren))
            case tok if tok in scanner.unary_op:
                unary = self.unary_op()
                term = self.term()
                return py_jack.ast.Term(term=(unary, term))
            case scanner.TokenType.IDENTIFIER:
                ident = self._next()
                LOGGER.debug(f"peeking: {self._peek()}")
                peek_result = self._peek()
                matcher = peek_result.token_type if peek_result else None
                match matcher:
                    case scanner.TokenType.LEFT_SQUARE_BRACKET:
                        # varName'[' expression ']'
                        LOGGER.debug("matched array index expression")
                        left_square_bracket = self._next()
                        expression = self.expression()
                        right_square_bracket = self._next()
                        return py_jack.ast.Term(
                            term=(
                                ident,
                                left_square_bracket,
                                expression,
                                right_square_bracket,
                            )
                        )
                    case scanner.TokenType.LEFT_PAREN | scanner.TokenType.DOT:
                        subroutine = self.subroutine_call(sub_name=ident)
                        return py_jack.ast.Term(term=subroutine)
                    case _:
                        LOGGER.debug("creating ident: %s", ident)
                        return py_jack.ast.Term(term=ident)
            case _:
                raise Exception("term did not match any rule")

    def unary_op(self):
        if self._peek().token_type not in scanner.unary_op:
            raise Exception(f"Expected a unary operator got {self._peek().token_type}")

        return self._next()

    def op(self):
        LOGGER.debug("parsing:op")
        if self._peek().token_type not in scanner.operations:
            raise Exception(f"Expected a operator got {self._peek().token_type}")

        return self._next()

    def keyword_constant(self):
        if self._peek().token_type not in scanner.keyword_constants:
            raise Exception(f"Expected keyword constant got {self._peek().token_type}")

        return self._next()

    def integer_constant(self):
        if self._peek().token_type != scanner.TokenType.INTEGER_CONSTANT:
            raise Exception(f"Expected integer constant got {self._peek().token_type}")

        return self._next()

    def string_constant(self):
        if self._peek().token_type != scanner.TokenType.STRING_CONSTANT:
            raise Exception(f"Expected string constant got {self._peek().token_type}")

        return self._next()

    def subroutine_call(self, sub_name):
        # figure out how this will work with term... it will start from (
        top = self._peek()
        matcher = top.token_type if top else None
        match matcher:
            case scanner.TokenType.DOT:
                dot = self._next()
                subroutine_name = self._next()
                # left_paren = self._next()
                expression_list = self.expression_list()
                # right_paren = self._next()
                return py_jack.ast.SubroutineCall(
                    subroutine_source=sub_name,
                    subroutine_name=subroutine_name,
                    expression_list=expression_list,
                )
            case scanner.TokenType.LEFT_PAREN:
                # left_paren = self._next()
                expression_list = self.expression_list()
                # right_paren = self._next()
                return py_jack.ast.SubroutineCall(
                    subroutine_name=sub_name, expression_list=expression_list
                )
            case _:
                raise Exception("should never happen")

    def expression_list(self):
        LOGGER.debug(("-----" * 8) + "[expression_list]" + ("-----" * 8))
        left_paren = self._next()
        if left_paren.token_type != scanner.TokenType.LEFT_PAREN:
            raise Exception("Expected ( but got %s", left_paren)
        token = self._peek()
        matcher = token.token_type if token else None
        match matcher:
            case scanner.TokenType.RIGHT_PAREN:
                right_paren = self._next()
                return py_jack.ast.ExpressionList()
            case _:
                expression = self.expression()
                expressions = []
                while (
                    top := self._peek()
                ) and top.token_type == scanner.TokenType.COMMA:
                    comma = self._next()
                    next_expression = self.expression()
                    expressions.append((comma, next_expression))

                right_paren = self._next()
                return py_jack.ast.ExpressionList(
                    expression=expression,
                    expression_list=functools.reduce(
                        lambda acc, val: acc + [val[1]], expressions, []
                    ),
                )
