from __future__ import annotations
import py_jack.scanner as scanner
import pathlib
import typing
import dataclasses


class XmlWriter(typing.Protocol):
    def write_xml(self, file: typing.IO, indent: int = 0): ...
    def write_token(self, token: scanner.Token, file: typing.IO, indent: int = 0):
        if token.token_type in scanner.token_variants["keywords"]:
            file.write(f"{'\t' * indent}<keyword> {token.lexeme} </keyword>\n")
        elif token.token_type in scanner.token_variants["symbols"]:
            file.write(f"{'\t' * indent}<symbol> {token.lexeme} </symbol>\n")
        else:
            file.write(
                f"{'\t' * indent}<{token.token_type.name.lower()}> {token.lexeme} </{token.token_type.name.lower()}>\n"
            )

    def write_string(
        self, surround: str, element: str, file: typing.IO, indent: int = 0
    ):
        file.write(f"{'\t' * indent}<{surround}> {element} </{surround}>\n")

    def write_node(self, file, indent: int, is_opening_tag: bool = True):
        if is_opening_tag:
            file.write(f"{'\t' * indent}<{type(self).__name__.lower()}>\n")
        else:
            file.write(f"{'\t' * indent}</{type(self).__name__.lower()}>\n")


@dataclasses.dataclass
class ClassNode(XmlWriter):
    class_kw: scanner.Token
    class_name: scanner.Token
    left_squerly: scanner.Token
    right_squerly: scanner.Token
    class_var_dec: list[ClassVarDec] | None = None
    subroutine_dec: list[SubroutineDec] | None = None

    def __repr__(self):
        return f"{self.__class__.__name__}( class {self.class_name.lexeme} {{ }} len: {len(self.class_var_dec)})"

    # why pass a file? Why not return a string or write to stdout? Could also be useful.
    def write_xml(self, file_path: pathlib.Path, indent: int):
        mode = "w"
        # if file_path.exists():
        #     mode = "w"
        with file_path.open(mode) as xml_file:
            xml_file.write(f"<{self.class_kw.lexeme}>\n")
            self.write_token(self.class_kw, xml_file, indent=indent)
            self.write_token(self.class_name, xml_file, indent=indent)
            self.write_string(
                "symbol", self.left_squerly.lexeme, xml_file, indent=indent
            )
            for class_var_dec in self.class_var_dec or []:
                class_var_dec.write_xml(xml_file, indent=indent)

            for subroutine_dec in self.subroutine_dec or []:
                subroutine_dec.write_xml(xml_file, indent=indent)
            self.write_string(
                "symbol", self.right_squerly.lexeme, xml_file, indent=indent
            )
            xml_file.write(f"</{self.class_kw.lexeme}>\n")


@dataclasses.dataclass
class ClassVarDec(XmlWriter):
    field_type: scanner.Token
    type_: scanner.Token
    var_name: scanner.Token
    semi_colon: scanner.Token
    var_names: list[tuple[scanner.Token, scanner.Token]] | None = None

    def write_xml(self, file: typing.IO, indent: int):
        file.write(f"{'\t' * indent}<classVarDec>\n")
        indent += 1
        self.write_token(self.field_type, file, indent=indent)
        self.write_token(self.type_, file, indent=indent)
        self.write_token(self.var_name, file, indent=indent)

        for comma, var_name in self.var_names or []:
            self.write_token(var_name, file, indent=indent)
            self.write_token(comma, file, indent=indent)

        self.write_string("symbol", self.semi_colon.lexeme, file=file, indent=indent)
        file.write(f"{'\t' * (indent - 1)}</classVarDec>\n")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}( {self.field_type}  | {self.field_type} | {self.var_name}) "


@dataclasses.dataclass
class SubroutineDec(XmlWriter):
    subroutine_variant: scanner.Token
    return_type: scanner.Token
    name: scanner.Token
    left_paren: scanner.Token
    right_paren: scanner.Token
    subroutine_body: SubroutineBody
    parameter_list: ParameterList

    def write_xml(self, file: typing.IO, indent: int):
        self.write_node(file, indent=indent)
        indent += 1
        self.write_token(self.subroutine_variant, file, indent)
        self.write_token(self.return_type, file, indent)
        self.write_token(self.name, file, indent)
        self.write_token(self.left_paren, file, indent)
        self.parameter_list.write_xml(file, indent)
        self.write_token(self.right_paren, file, indent)
        # TODO: stopped here
        self.write_node(file, indent=indent, is_opening_tag=False)


@dataclasses.dataclass
class ParameterList(XmlWriter):
    _type: scanner.Token | None = None
    varname: scanner.Token | None = None
    parameters: list[tuple[scanner.Token, scanner.Token, scanner.Token]] = (
        dataclasses.field(default_factory=list)
    )

    def write_xml(self, file: typing.IO, indent: int = 0):
        self.write_node(
            file, indent
        )  # is this not a great place for a context manager????
        if self._type is None or self.varname is None:
            self.write_node(file, indent, is_opening_tag=False)
            return
        indent += 1
        self.write_token(self._type, file, indent)
        self.write_token(self.varname, file, indent)
        for comma, next_type, next_varname in self.parameters:
            self.write_token(comma, file, indent)
            self.write_token(next_type, file, indent)
            self.write_token(next_varname, file, indent)
        self.write_node(file, indent, is_opening_tag=False)


@dataclasses.dataclass
class VarDec(XmlWriter):
    var_kw: scanner.Token
    _type: scanner.Token
    var_name: scanner.Token
    var_names: list[tuple[scanner.Token, scanner.Token]]
    semi_colon: scanner.Token

    def write_xml(self, file: typing.IO, indent: int):
        raise NotImplementedError("not implemented")


@dataclasses.dataclass
class SubroutineBody(XmlWriter):
    left_squerly: scanner.Token
    var_decs: list[VarDec]
    statements: list[Statement]
    right_squerly: scanner.Token

    def write_xml(self, file: typing.IO, indent: int):
        raise NotImplementedError("not implemented")


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


type Statement = (
    LetStatement | IfStatement | WhileStatement | DoStatement | ReturnStatement
)


@dataclasses.dataclass
class ReturnStatement(XmlWriter):
    return_kw: scanner.Token
    semicolon: scanner.Token
    expression: Expression | None = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        raise NotImplementedError("not working yet")


@dataclasses.dataclass
class DoStatement(XmlWriter):
    do_kw: scanner.Token
    subroutine_call: SubroutineCall
    semicolon: scanner.Token

    def write_xml(self, file: typing.IO, indent: int = 0):
        raise NotImplementedError("not working yet")


@dataclasses.dataclass
class LetStatement(XmlWriter):
    let_kw: scanner.Token
    var_name: scanner.Token
    equal: scanner.Token
    expression: Expression
    semi_colon: scanner.Token
    index_var: tuple[scanner.Token, Expression, scanner.Token] | None = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        raise NotImplementedError("not working yet")


@dataclasses.dataclass
class IfStatement(XmlWriter):
    if_kw: scanner.Token
    left_paren: scanner.Token
    expression: Expression
    right_paren: scanner.Token
    left_curly: scanner.Token
    right_curly: scanner.Token
    statements: list[Statement] | None = None
    optional_else: (
        tuple[scanner.Token, scanner.Token, list[Statement], scanner.Token] | None
    ) = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        raise NotImplementedError("not working yet")


@dataclasses.dataclass
class WhileStatement(XmlWriter):
    while_kw: scanner.Token
    left_paren: scanner.Token
    expression: Expression
    right_paren: scanner.Token
    left_curly: scanner.Token
    right_curly: scanner.Token
    statements: list[Statement] | None = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        raise NotImplementedError("not working yet")
