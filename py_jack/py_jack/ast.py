from __future__ import annotations
import py_jack.scanner as scanner
import pathlib
import typing
import dataclasses


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


type Statement = (
    LetStatement | IfStatement | WhileStatement | DoStatement | ReturnStatement
)


@dataclasses.dataclass
class ReturnStatement(XmlWriter):
    return_kw: scanner.Token
    expression: Expression
    semicolon: scanner.Token

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
