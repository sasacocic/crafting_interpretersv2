from __future__ import annotations
from collections.abc import Iterator
import py_jack.scanner as scanner
import logging
import itertools
import pathlib
import typing
import dataclasses
import functools

LOGGER = logging.getLogger(__name__)


class XmlWriter(typing.Protocol):
    def write_xml(self, file: typing.IO, indent: int = 0): ...
    def write_token(self, token: scanner.Token, file: typing.IO, indent: int = 0):
        if token.token_type in scanner.Scanner.keywords.values():
            file.write(f"{'\t' * indent}<keyword> {token.lexeme} </keyword>\n")
        else:
            file.write(
                f"{'\t' * indent}<{token.token_type.name.lower()}> {token.lexeme} </{token.token_type.name.lower()}>\n"
            )

    def write_string(
        self, surround: str, element: str, file: typing.IO, indent: int = 0
    ):
        file.write(f"{'\t' * indent}<{surround}> {element} </{surround}>\n")


class ClassNode(XmlWriter):
    class_name: scanner.Token
    class_var_dec: list[ClassVarDec] | None

    def __init__(
        self, class_name: scanner.Token, class_var_dec: list[ClassVarDec] | None = None
    ) -> None:
        self.class_name = class_name
        self.class_var_dec = class_var_dec

    def __repr__(self):
        return f"{self.__class__.__name__}( class {self.class_name.lexeme} {{ }} len: {len(self.class_var_dec)})"

    # why pass a file? Why not return a string or write to stdout? Could also be useful.
    def write_xml(self, file_path: pathlib.Path, indent: int):
        mode = "w"
        # if file_path.exists():
        #     mode = "w"
        with file_path.open(mode) as xml_file:
            xml_file.write("<class>\n")
            xml_file.write(f"{'\t' * indent}<keyword> class </keyword>\n")
            self.write_token(self.class_name, xml_file, indent=indent)
            self.write_string("symbol", "{", xml_file, indent=indent)
            for class_var_dec in self.class_var_dec:
                class_var_dec.write_xml(xml_file, indent=indent)
            xml_file.write("</class>\n")


class ClassVarDec(XmlWriter):
    field_type: scanner.Token
    type_: scanner.Token
    var_name: list[scanner.Token] | None

    def __init__(
        self,
        field_type: scanner.Token,
        type_: scanner.Token,
        var_name: list[scanner.Token],
    ) -> None:
        self.field_type = field_type
        self.type_ = type_
        self.var_name = var_name

    def write_xml(self, file: typing.IO, indent: int):
        file.write(f"{'\t' * indent}<classVarDec>\n")
        indent += 1
        self.write_token(self.field_type, file, indent=indent)
        self.write_token(self.type_, file, indent=indent)
        for var_name in self.var_name:
            self.write_token(var_name, file, indent=indent)
            file.write(
                f"{'\t' * indent}<symbol> , </symbol>\n"
            )  # TODO: I know this is wrong. The last iteration I don't want to add a comma

        file.write(f"{'\t' * indent}<symbol> ; </symbol>\n")
        file.write(f"{'\t' * indent}</classVarDec>\n")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}( {self.field_type}  | {self.field_type} | {self.var_name}) "


class SubroutineDec(XmlWriter):
    subroutine_type: scanner.Token
    return_type: scanner.Token
    name: scanner.Token
    parameter_list: None = None
    subroutine_body: None = None


@dataclasses.dataclass
class ParameterList(XmlWriter):
    parameters: list[tuple[scanner.Token, scanner.Token]]

    def write_xml(self, file: typing.IO, indent: int = 0):
        raise NotImplementedError("not working yet")


@dataclasses.dataclass
class Expression(XmlWriter):
    term: Term
    op_terms: list[tuple[scanner.Token, Term]]

    def write_xml(self, file: typing.IO, indent: int = 0):
        raise NotImplementedError("not working yet")


@dataclasses.dataclass
class Term(XmlWriter):
    # terms: scanner.Token | ArrayOperation | subroutineCall | '(' expression ')' | expressionList
    term: (
        scanner.Token
        | tuple[scanner.Token, Term]
        | tuple[scanner.Token, Expression, scanner.Token]
        | tuple[scanner.Token, scanner.Token, Expression, scanner.Token]
        | SubroutineCall
    )

    def write_xml(self, file: typing.IO, indent: int = 0):
        raise NotImplementedError("not working yet")


@dataclasses.dataclass
class ExpressionList(XmlWriter):
    expression: Expression | None = None
    expression_list: list[Expression] | None = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        raise NotImplementedError("not working yet")


@dataclasses.dataclass
class SubroutineCall(XmlWriter):
    subroutine_name: scanner.Token
    subroutine_source: scanner.Token | None = None
    expression_list: ExpressionList = dataclasses.field(
        default_factory=lambda: ExpressionList()
    )

    def write_xml(self, file: typing.IO, indent: int = 0):
        raise NotImplementedError("not working yet")


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
        new_one, copy = itertools.tee(self.token_iter)
        self.token_iter = new_one  # have to do this with tee - they say not to use the original anymore
        return next(copy, None)

    def parse(self):
        return self.parse_class()

    def parse_class(self) -> ClassNode:
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
                return ClassNode(class_name=class_name, class_var_dec=[class_var_dec])
            case _:
                raise Exception("didn't start with class keyword")

    def parse_class_name(self):
        class_name = self._next()
        if class_name.token_type != scanner.TokenType.IDENTIFIER:
            raise Exception(f"{class_name} not an identifier")
        return class_name

    def parse_class_var_dec(self) -> ClassVarDec:
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

        cvd = ClassVarDec(field_type=field_type, type_=type_, var_name=[varname])
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

    def parse_parameter_list(self) -> ParameterList:
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

        return ParameterList(parameters=type_var_name)

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

    # expression parsing

    def expression(self):
        LOGGER.debug(f"expression:tokens: {self.tokens}")
        term = self.term()
        ops_and_terms = []
        while (top := self._peek()) and top.token_type in scanner.operations:
            ops_and_terms.append((self.op(), self.term()))
        return Expression(term=term, op_terms=ops_and_terms)

    def term(self) -> Term:
        LOGGER.debug(f"term:tokens: {self.tokens}")
        top = self._peek()
        matcher = top.token_type if top else None
        match matcher:
            case scanner.TokenType.STRING_CONSTANT:
                return Term(term=self.string_constant())
            case scanner.TokenType.INTEGER_CONSTANT:
                return Term(term=self.integer_constant())
            case token if token in scanner.keyword_constants:
                return Term(term=self.keyword_constant())
            case scanner.TokenType.LEFT_PAREN:
                left_paren = self._next()
                expression = self.expression()
                right_paren = self._next()
                if right_paren.token_type != scanner.TokenType.RIGHT_PAREN:
                    raise Exception("expected right paren - didn't recieve")
                return Term(term=(left_paren, expression, right_paren))
            case tok if tok in scanner.unary_op:
                unary = self.unary_op()
                term = self.term()
                return Term(term=(unary, term))
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
                        return Term(
                            term=(
                                ident,
                                left_square_bracket,
                                expression,
                                right_square_bracket,
                            )
                        )
                    case scanner.TokenType.LEFT_PAREN | scanner.TokenType.DOT:
                        subroutine = self.subroutine_call(sub_name=ident)
                        return Term(term=subroutine)
                    case _:
                        LOGGER.debug("creating ident: %s", ident)
                        return Term(term=ident)
            case _:
                raise Exception("term did not match any rule")

    def unary_op(self):
        if self._peek().token_type not in scanner.unary_op:
            raise Exception(f"Expected a unary operator got {self._peek().token_type}")

        return self._next()

    def op(self):
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
                right_paren = self._next()
                return SubroutineCall(
                    subroutine_source=sub_name,
                    subroutine_name=subroutine_name,
                    expression_list=expression_list,
                )
            case scanner.TokenType.LEFT_PAREN:
                # left_paren = self._next()
                expression_list = self.expression_list()
                right_paren = self._next()
                return SubroutineCall(
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
                self._next()
                return ExpressionList()
            case _:
                expression = self.expression()
                expressions = []
                while (
                    top := self._peek()
                ) and top.token_type == scanner.TokenType.COMMA:
                    comma = self._next()
                    next_expression = self.expression()
                    expressions.append((comma, next_expression))

                return ExpressionList(
                    expression=expression,
                    expression_list=functools.reduce(
                        lambda acc, val: acc + [val[1]], expressions, []
                    ),
                )
