from __future__ import annotations
from collections.abc import Iterator
import py_jack.jack_scanner as jack_scanner
import logging
import itertools
import py_jack.ast_nodes

LOGGER = logging.getLogger(__name__)


class Parser:
    """
    recursive descent parser
    """

    tokens: list[jack_scanner.Token]
    token_iter: Iterator[jack_scanner.Token]

    def __init__(self, tokens: list[jack_scanner.Token]) -> None:
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
        """
        TODO: need to change this. I'm basically using this as the entry point into to reset the symbol
        tables. There's definitely a more buttoned up way to do this than this.
        """
        py_jack.ast_nodes.class_occurrences = {
            "field": 0,
            "static": 0,
            "local": 0,
            "argument": 0,
            # there are more of these just not really sure about them
        }
        py_jack.ast_nodes.class_symbols = {}
        py_jack.ast_nodes.current_class_name = None
        py_jack.ast_nodes.current_subroutine_name = None
        return self.parse_class()

    def parse_class(self) -> py_jack.ast_nodes.ClassNode:
        class_kw = self._next()
        match class_kw.lexeme:
            case "class":
                class_name = self.parse_class_name()
                left_squerly = self._next()
                class_var_dec = []
                while self._peek_token_type() in [
                    jack_scanner.TokenType.STATIC,
                    jack_scanner.TokenType.FIELD,
                ]:
                    class_var_dec.append(self.parse_class_var_dec())

                subroutine_decs = []
                while self._peek_token_type() in [
                    jack_scanner.TokenType.CONSTRUCTOR,
                    jack_scanner.TokenType.FUNCTION,
                    jack_scanner.TokenType.METHOD,
                ]:
                    subroutine_decs.append(self.subroutine_dec())

                right_squerly = self._next()

                class_var_dec = class_var_dec if class_var_dec else None
                subroutine_decs = subroutine_decs if subroutine_decs else None
                return py_jack.ast_nodes.ClassNode(
                    class_kw,
                    class_name,
                    left_squerly,
                    right_squerly,
                    class_var_dec,
                    subroutine_decs,
                )
            case _:
                raise Exception("didn't start with class keyword")

    def parse_class_name(self):
        class_name = self._next()
        if class_name.token_type != jack_scanner.TokenType.IDENTIFIER:
            raise Exception(f"{class_name} not an identifier")
        return class_name

    def parse_class_var_dec(self) -> py_jack.ast_nodes.ClassVarDec:
        field_type = self._next()
        if not any([
            field_type.lexeme == valid_lexeme for valid_lexeme in ["static", "field"]
        ]):
            raise Exception(
                f"{field_type} - not valid. Needs to be 'static' or 'field'"
            )

        type_ = self.parse_type()
        varname = self.parse_varname()
        varnames = []
        while self._peek_token_type() == jack_scanner.TokenType.COMMA:
            comma = self._next()
            var_name = self._next()  # varname's are just identifiers
            varnames.append((comma, var_name))
        semi_colon = self._next()
        if semi_colon.lexeme != ";":
            raise Exception(f"expected ';', but found {semi_colon}")

        cvd = py_jack.ast_nodes.ClassVarDec(
            field_type=field_type,
            type_=type_,
            var_name=varname,
            var_names=varnames,
            semi_colon=semi_colon,
        )
        return cvd

    def subroutine_dec(self):
        sub_variant = self._next()
        if sub_variant.token_type not in [
            jack_scanner.TokenType.CONSTRUCTOR,
            jack_scanner.TokenType.FUNCTION,
            jack_scanner.TokenType.METHOD,
        ]:
            raise Exception("invalid subroutine type")

        sub_return_type = self._next()
        LOGGER.debug("asserting %s is void or a type", sub_return_type)
        assert (
            sub_return_type.token_type == jack_scanner.TokenType.VOID
            or sub_return_type.token_type in jack_scanner.type_tokens
        )

        routine_name = self._next()

        left_paren = self._next()
        parameter_list = self.parse_parameter_list()
        right_paren = self._next()

        routine_body = self.subroutine_body()

        return py_jack.ast_nodes.SubroutineDec(
            subroutine_variant=sub_variant,
            return_type=sub_return_type,
            name=routine_name,
            left_paren=left_paren,
            parameter_list=parameter_list,
            right_paren=right_paren,
            subroutine_body=routine_body,
        )

    def parse_parameter_list(self) -> py_jack.ast_nodes.ParameterList | None:
        if self._peek_token_type() == jack_scanner.TokenType.RIGHT_PAREN:
            return py_jack.ast_nodes.ParameterList()

        _type = self._next()
        var_name = self._next()

        type_var_name = []

        while self._peek_token_type() == jack_scanner.TokenType.COMMA:
            comma = self._next()
            next_type = self._next()
            next_var_name = self._next()
            assert var_name.token_type == jack_scanner.TokenType.IDENTIFIER
            type_var_name.append((comma, next_type, next_var_name))
        else:
            LOGGER.info(
                "parameter_list ending with: %s - not in %s",
                self._peek_token_type(),
                jack_scanner.type_tokens,
            )

        return py_jack.ast_nodes.ParameterList(
            _type=_type, varname=var_name, parameters=type_var_name
        )

    def var_dec(self):
        var_kw = self._next()
        if var_kw.token_type != jack_scanner.TokenType.VAR:
            raise Exception(f"expected 'var' keyword, got: {var_kw}")
        _type = self.parse_type()
        var_name = self._next()
        var_names = []
        while self._peek_token_type() == jack_scanner.TokenType.COMMA:
            var_names.append((self._next(), self._next()))
        semi_colon = self._next()
        return py_jack.ast_nodes.VarDec(
            var_kw=var_kw,
            _type=_type,
            var_name=var_name,
            var_names=var_names,
            semi_colon=semi_colon,
        )

    def subroutine_body(self):
        left_squerly = self._next()
        var_decs = []
        while self._peek_token_type() == jack_scanner.TokenType.VAR:
            var_decs.append(self.var_dec())
        statements = self.parse_statements()
        right_squerly = self._next()
        return py_jack.ast_nodes.SubroutineBody(
            left_squerly, var_decs, statements, right_squerly
        )

    def parse_type(self):
        token = self._next()

        if not any([
            token.token_type == valid_token_type
            for valid_token_type in [
                jack_scanner.TokenType.INT,
                jack_scanner.TokenType.CHAR,
                jack_scanner.TokenType.BOOLEAN,
                jack_scanner.TokenType.IDENTIFIER,
            ]
        ]):
            raise Exception(f"{token} - not valid. Needs to be 'static' or 'field'")

        return token

    def parse_varname(self) -> jack_scanner.Token:
        token = self._next()

        if token.token_type != jack_scanner.TokenType.IDENTIFIER:
            raise Exception(f"{token} - not valid. Needs to be an identifier")

        return token

    # statment parsing

    def parse_constant(self):
        constant = self._next()
        assert constant.token_type in jack_scanner.literals
        return constant

    def parse_statements(self) -> py_jack.ast_nodes.Statements:
        LOGGER.info("parser:parse_statements")
        statements: list[py_jack.ast_nodes.StatementType] = []
        LOGGER.info(self._peek_token_type())
        LOGGER.info(self._peek().lexeme)
        while self._peek_token_type() in jack_scanner.statements:
            LOGGER.info("parsing %s", self._peek_token_type().name)
            statements.append(self.statement())
        return py_jack.ast_nodes.Statements(statements=statements)

    def statement(self) -> py_jack.ast_nodes.StatementType:
        statement = None
        match self._peek_token_type():
            case jack_scanner.TokenType.LET:
                statement = self.let_statement()
            case jack_scanner.TokenType.IF:
                statement = self.if_statement()
            case jack_scanner.TokenType.WHILE:
                statement = self.while_statement()
            case jack_scanner.TokenType.DO:
                statement = self.do_statement()
            case jack_scanner.TokenType.RETURN:
                statement = self.return_statement()
            case _:
                raise Exception("statment didn't match one of the statements")

        return statement

    def if_statement(self) -> py_jack.ast_nodes.IfStatement:
        if_kw = self._next()
        l_paren = self._next()
        expression = self.expression()
        r_paren = self._next()
        l_curly = self._next()
        statements = self.parse_statements()
        r_curly = self._next()
        if_statement = py_jack.ast_nodes.IfStatement(
            if_kw=if_kw,
            left_paren=l_paren,
            expression=expression,
            right_paren=r_paren,
            left_curly=l_curly,
            statements=statements,
            right_curly=r_curly,
        )

        if (
            else_kw := self._peek_token_type()
        ) and else_kw == jack_scanner.TokenType.ELSE:
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

    def while_statement(self) -> py_jack.ast_nodes.WhileStatement:
        while_kw = self._next()
        l_paren = self._next()
        expression = self.expression()
        r_paren = self._next()
        l_curly = self._next()
        statements = self.parse_statements()
        r_curly = self._next()
        return py_jack.ast_nodes.WhileStatement(
            while_kw=while_kw,
            left_paren=l_paren,
            expression=expression,
            right_paren=r_paren,
            left_curly=l_curly,
            statements=statements,
            right_curly=r_curly,
        )

    def return_statement(self) -> py_jack.ast_nodes.ReturnStatement:
        return_kw = self._next()
        if return_kw.token_type != jack_scanner.TokenType.RETURN:
            raise Exception("expected return keyword - didn't get it")

        if self._peek_token_type() == jack_scanner.TokenType.SEMICOLON:
            semi_colon = self._next()
            return py_jack.ast_nodes.ReturnStatement(
                return_kw=return_kw, semicolon=semi_colon
            )
        expression = self.expression()
        semi_colon = self._next()
        return py_jack.ast_nodes.ReturnStatement(
            return_kw=return_kw, expression=expression, semicolon=semi_colon
        )

    def do_statement(self) -> py_jack.ast_nodes.DoStatement:
        do_kw = self._next()
        if do_kw.token_type != jack_scanner.TokenType.DO and do_kw.lexeme != "do":
            raise Exception("expected do keyword - didn't get it")

        subroutine_ident = self._next()
        subroutine = self.subroutine_call(sub_name=subroutine_ident)
        semi_colon = self._next()
        return py_jack.ast_nodes.DoStatement(
            do_kw=do_kw, subroutine_call=subroutine, semicolon=semi_colon
        )

    def let_statement(self) -> py_jack.ast_nodes.LetStatement:
        LOGGER.info("parsing:let_statement")
        let_kw = self._next()
        if let_kw.token_type != jack_scanner.TokenType.DO and let_kw.lexeme != "let":
            raise Exception("expected let keyword - didn't get it")

        ident = self._next()
        match self._peek().token_type:
            case jack_scanner.TokenType.LEFT_SQUARE_BRACKET:
                left_square = self._next()
                optional_expr = self.expression()
                right_square = self._next()
                equal = self._next()
                expr = self.expression()
                semi_colon = self._next()

                return py_jack.ast_nodes.LetStatement(
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
                return py_jack.ast_nodes.LetStatement(
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
        while (top := self._peek()) and top.token_type in jack_scanner.operations:
            LOGGER.debug("looking at (op term)*")
            ops_and_terms.append((self.op(), self.term()))
        return py_jack.ast_nodes.Expression(term=term, op_terms=ops_and_terms)

    def term(self) -> py_jack.ast_nodes.Term:
        LOGGER.debug(f"term:tokens: {self.tokens}")
        top = self._peek()
        matcher = top.token_type if top else None
        match matcher:
            case jack_scanner.TokenType.STRING_CONSTANT:
                return py_jack.ast_nodes.Term(term=self.string_constant())
            case jack_scanner.TokenType.INTEGER_CONSTANT:
                return py_jack.ast_nodes.Term(term=self.integer_constant())
            case token if token in jack_scanner.keyword_constants:
                return py_jack.ast_nodes.Term(term=self.keyword_constant())
            case jack_scanner.TokenType.LEFT_PAREN:
                left_paren = self._next()
                expression = self.expression()
                right_paren = self._next()
                if right_paren.token_type != jack_scanner.TokenType.RIGHT_PAREN:
                    raise Exception("expected right paren - didn't recieve")
                return py_jack.ast_nodes.Term(
                    term=(left_paren, expression, right_paren)
                )
            case tok if tok in jack_scanner.unary_op:
                unary = self.unary_op()
                term = self.term()
                return py_jack.ast_nodes.Term(term=(unary, term))
            case jack_scanner.TokenType.IDENTIFIER:
                ident = self._next()
                LOGGER.debug(f"peeking: {self._peek()}")
                peek_result = self._peek()
                matcher = peek_result.token_type if peek_result else None
                match matcher:
                    case jack_scanner.TokenType.LEFT_SQUARE_BRACKET:
                        # varName'[' expression ']'
                        LOGGER.debug("matched array index expression")
                        left_square_bracket = self._next()
                        expression = self.expression()
                        right_square_bracket = self._next()
                        return py_jack.ast_nodes.Term(
                            term=(
                                ident,
                                left_square_bracket,
                                expression,
                                right_square_bracket,
                            )
                        )
                    case jack_scanner.TokenType.LEFT_PAREN | jack_scanner.TokenType.DOT:
                        subroutine = self.subroutine_call(sub_name=ident)
                        return py_jack.ast_nodes.Term(term=subroutine)
                    case _:
                        LOGGER.debug("creating ident: %s", ident)
                        return py_jack.ast_nodes.Term(term=ident)
            case _:
                raise Exception(f"{matcher}: term did not match any rule")

    def unary_op(self):
        if self._peek().token_type not in jack_scanner.unary_op:
            raise Exception(f"Expected a unary operator got {self._peek().token_type}")

        return self._next()

    def op(self):
        LOGGER.debug("parsing:op")
        if self._peek().token_type not in jack_scanner.operations:
            raise Exception(f"Expected a operator got {self._peek().token_type}")

        return self._next()

    def keyword_constant(self):
        if self._peek().token_type not in jack_scanner.keyword_constants:
            raise Exception(f"Expected keyword constant got {self._peek().token_type}")

        return self._next()

    def integer_constant(self):
        if self._peek().token_type != jack_scanner.TokenType.INTEGER_CONSTANT:
            raise Exception(f"Expected integer constant got {self._peek().token_type}")

        return self._next()

    def string_constant(self):
        if self._peek().token_type != jack_scanner.TokenType.STRING_CONSTANT:
            raise Exception(f"Expected string constant got {self._peek().token_type}")

        return self._next()

    def subroutine_call(self, sub_name):
        # figure out how this will work with term... it will start from (
        top = self._peek()
        matcher = top.token_type if top else None
        match matcher:
            case jack_scanner.TokenType.DOT:
                dot = self._next()
                subroutine_name = self._next()
                left_paren = self._next()
                expression_list = self.expression_list()
                right_paren = self._next()
                return py_jack.ast_nodes.SubroutineCall(
                    subroutine_source=sub_name,
                    dot=dot,
                    subroutine_name=subroutine_name,
                    expression_list=expression_list,
                    left_paren=left_paren,
                    right_paren=right_paren,
                )
            case jack_scanner.TokenType.LEFT_PAREN:
                left_paren = self._next()
                expression_list = self.expression_list()
                right_paren = self._next()
                return py_jack.ast_nodes.SubroutineCall(
                    subroutine_name=sub_name,
                    expression_list=expression_list,
                    left_paren=left_paren,
                    right_paren=right_paren,
                )
            case _:
                raise Exception("should never happen")

    def expression_list(self):
        LOGGER.debug(("-----" * 8) + "[expression_list]" + ("-----" * 8))
        token = self._peek()
        matcher = token.token_type if token else None
        match matcher:
            case jack_scanner.TokenType.RIGHT_PAREN:
                return py_jack.ast_nodes.ExpressionList()
            case _:
                expression = self.expression()
                expressions: list[
                    tuple[jack_scanner.Token, py_jack.ast_nodes.Expression]
                ] = []
                while (
                    top := self._peek()
                ) and top.token_type == jack_scanner.TokenType.COMMA:
                    comma = self._next()
                    next_expression = self.expression()
                    expressions.append((comma, next_expression))

                return py_jack.ast_nodes.ExpressionList(
                    expression=expression,
                    expression_list=expressions,
                )
