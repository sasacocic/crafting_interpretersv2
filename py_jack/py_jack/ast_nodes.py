from __future__ import annotations
import py_jack.jack_scanner as jack_scanner
import pathlib
import typing
import dataclasses
import contextlib
import logging


LOGGER: typing.Final = logging.getLogger(__name__)


class CodeGenWriter[T: typing.IO]:
    _file: T

    def __init__(self, io: T):
        self._file = io

    def write_code(self, indent: int, code_stream: str):
        self._file.write(f"{indent * " "}{code_stream}\n")


@dataclasses.dataclass(frozen=True)
class VariableInfo:
    type_: str  # int, bool, char, ClassName
    kind: str  # static, field, local, etc.
    occurrence: int  # occurance of thing


current_class_name: str | None = None
class_occurrences: dict[str, int] = {
    "field": 0,
    "static": 0,
    "local": 0,
    "argument": 0,
    "class": 0,
    # there are more of these just not really sure about them
}

class_symbols: dict[str, VariableInfo] = {}
current_subroutine_name: str | None = None
subroutine_occurrences: dict[str, int] = {
    "field": 0,
    "static": 0,
    "local": 0,
    "argument": 0,
    "subroutine": 0,
}


def reset_subroutine_occurrences():
    global subroutine_occurrences
    subroutine_occurrences = {
        "field": 0,
        "static": 0,
        "local": 0,
        "argument": 0,
        "subroutine": 0,
    }
    # yield None  # do I need to yield anything?


subroutine_symbols: dict[str, VariableInfo] = {}


class ASTEval(typing.Protocol):
    def eval_node(self, file: typing.IO):
        pass

    def write_eval(self, file: typing.IO):
        pass


class XmlWriter(typing.Protocol):
    def write_xml(self, file: typing.IO, indent: int = 0):
        pass

    def write_token(self, token: jack_scanner.Token, file: typing.IO, indent: int = 0):
        if token.token_type in jack_scanner.token_variants["keywords"]:
            file.write(f"{' ' * indent}<keyword> {token.lexeme} </keyword>\n")
        elif token.token_type in jack_scanner.token_variants["symbols"]:
            match token.token_type:
                case jack_scanner.TokenType.AMPERSAND:
                    file.write(f"{' ' * indent}<symbol> {'&amp;'} </symbol>\n")
                case jack_scanner.TokenType.GREATER_THAN:
                    file.write(f"{' ' * indent}<symbol> {'&gt;'} </symbol>\n")
                case jack_scanner.TokenType.LESS_THAN:
                    file.write(f"{' ' * indent}<symbol> {'&lt;'} </symbol>\n")
                case jack_scanner.TokenType() if token.lexeme == '"':
                    file.write(f"{' ' * indent}<symbol> {'&quot;'} </symbol>\n")
                case _:
                    file.write(f"{' ' * indent}<symbol> {token.lexeme} </symbol>\n")
        elif token.token_type in [
            jack_scanner.TokenType.INTEGER_CONSTANT,
            jack_scanner.TokenType.STRING_CONSTANT,
        ]:
            tag = token.token_type.name.lower().split("_")
            new_tag = "".join([tag[0], tag[1][0].upper() + tag[1][1:]])
            file.write(f"{' ' * indent}<{new_tag}> {token.lexeme} </{new_tag}>\n")
        else:
            file.write(
                f"{' ' * indent}<{token.token_type.name.lower()}> {token.lexeme} </{token.token_type.name.lower()}>\n"
            )

    def write_string(
        self, surround: str, element: str, file: typing.IO, indent: int = 0
    ):
        file.write(f"{' ' * indent}<{surround}> {element} </{surround}>\n")

    @contextlib.contextmanager
    def write_node(self, file, indent: int):
        file.write(f"{' ' * indent}<{self.camel_case()}>\n")
        yield
        file.write(f"{' ' * indent}</{self.camel_case()}>\n")

    def camel_case(self):
        name = type(self).__name__
        return name[0].lower() + name[1:]


_code_gen_indent: int = 0


def get_code_gen_indent():
    global _code_gen_indent
    return _code_gen_indent


@contextlib.contextmanager
def code_gen_indent():
    global _code_gen_indent

    _code_gen_indent += 2

    yield _code_gen_indent
    _code_gen_indent -= 2


@dataclasses.dataclass
class ClassNode(XmlWriter, ASTEval):
    class_kw: jack_scanner.Token
    class_name: jack_scanner.Token
    left_squerly: jack_scanner.Token
    right_squerly: jack_scanner.Token
    class_var_dec: list[ClassVarDec] | None = None
    subroutine_dec: list[SubroutineDec] | None = None

    def __repr__(self):
        return f"{self.__class__.__name__}( class {self.class_name.lexeme} {{ }} len: {len(self.class_var_dec or [])})"

    # why pass a file? Why not return a string or write to stdout? Could also be useful.
    # def write_xml(self, file: typing.IO, indent: int = 0):
    def write_xml(self, file: pathlib.Path, indent: int = 0):
        LOGGER.debug(f"writing to: {file.name}")
        mode = "w"
        with file.open(mode) as xml_file:
            xml_file.write(f"<{self.class_kw.lexeme}>\n")
            indent += 1
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

    def compile(self, file: pathlib.Path):
        # assumes file is valid at least and will create it
        LOGGER.info(f"writing to: {file.resolve()}")
        mode = "w"
        with file.open(mode) as vm_code_file:
            self.eval_node(file=vm_code_file)

    def eval_node(self, file: typing.IO):
        LOGGER.debug("eval:ClassNode")
        global current_class_name
        current_class_name = self.class_name.lexeme

        for class_var_def in self.class_var_dec or []:
            # I stopped here - I need to iterate over the tree again - I should
            # be able to do this for really small portions
            class_var_def.eval_node(file)

        for subroutine_dec in self.subroutine_dec or []:
            subroutine_dec.eval_node(file)

    # def write_eval(self, file: typing.IO):
    #     self.eval_node()
    #     return super().write_eval(file, indent)


@dataclasses.dataclass
class ClassVarDec(XmlWriter, ASTEval):
    field_type: jack_scanner.Token
    type_: jack_scanner.Token
    var_name: jack_scanner.Token
    semi_colon: jack_scanner.Token
    var_names: list[tuple[jack_scanner.Token, jack_scanner.Token]] | None = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent=indent):
            indent += 2
            self.write_token(self.field_type, file, indent=indent)
            self.write_token(self.type_, file, indent=indent)
            self.write_token(self.var_name, file, indent=indent)

            for comma, var_name in self.var_names or []:
                self.write_token(comma, file, indent=indent)
                self.write_token(var_name, file, indent=indent)

            self.write_string(
                "symbol", self.semi_colon.lexeme, file=file, indent=indent
            )
        # file.write(f"{' ' * indent}</classVarDec>\n")

    def eval_node(self, file: typing.IO):
        vnames = [t for t in [self.var_name] + [e[1] for e in self.var_names or []]]
        for var_name in vnames:
            field_type_count = class_occurrences[self.field_type.lexeme]
            LOGGER.debug(
                "class_symbol: %s -> [%s, %s, %s]"
                % (
                    var_name.lexeme,
                    self.type_.lexeme,
                    self.field_type.lexeme,
                    field_type_count,
                )
            )
            # type, kind, occurrence
            class_symbols[var_name.lexeme] = VariableInfo(
                type_=self.type_.lexeme,
                kind=self.field_type.lexeme,
                occurrence=field_type_count,
            )
            class_occurrences[self.field_type.lexeme] = field_type_count + 1

        self.write_eval(file)

    def write_eval(self, file: typing.IO):
        vnames = [t for t in [self.var_name] + [e[1] for e in self.var_names or []]]
        for symbol in vnames:
            surround = "ClassVarDecSymbols"
            var_info = class_symbols[symbol.lexeme]
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}( {self.field_type}  | {self.field_type} | {self.var_name}) "


@dataclasses.dataclass
class SubroutineDec(XmlWriter, ASTEval):
    subroutine_variant: jack_scanner.Token
    return_type: jack_scanner.Token
    name: jack_scanner.Token
    left_paren: jack_scanner.Token
    right_paren: jack_scanner.Token
    subroutine_body: SubroutineBody
    parameter_list: ParameterList

    @property
    def symbol_name(self):
        return self.name.lexeme

    def write_xml(self, file: typing.IO, indent: int):
        # self.eval_node()
        # self.write_eval(file)
        with self.write_node(file, indent=indent):
            indent += 2
            self.write_token(self.subroutine_variant, file, indent)
            self.write_token(self.return_type, file, indent)
            self.write_token(self.name, file, indent)
            self.write_token(self.left_paren, file, indent)
            self.parameter_list.write_xml(file, indent)
            self.write_token(self.right_paren, file, indent)
            self.subroutine_body.write_xml(file, indent)
            # self.write_node(file, indent=indent, is_opening_tag=False)

    def eval_node(self, file: typing.IO):
        with code_gen_indent():
            LOGGER.debug("eval:SubroutineDec")
            global current_subroutine_name
            current_subroutine_name = self.name.lexeme

            global subroutine_symbols
            subroutine_symbols = {}
            reset_subroutine_occurrences()
            LOGGER.info(f"compiling subroutine: {current_subroutine_name}")
            self.write_eval(file)

    def write_eval(self, file: typing.IO):
        LOGGER.debug("write:SubroutineDec")
        global current_class_name
        global current_subroutine_name

        self.parameter_list.eval_node(file)

        local_argument_count = (
            self.subroutine_body.variable_declaration_count
        )  # arguments to a function are not considered local variables

        file.write(
            f"function {current_class_name}.{current_subroutine_name} {local_argument_count}\n"
        )
        self.subroutine_body.eval_node(file)


class ParameterVar(typing.NamedTuple):
    type_: str
    varname: str


@dataclasses.dataclass
class ParameterList(XmlWriter, ASTEval):
    _type: jack_scanner.Token | None = None
    varname: jack_scanner.Token | None = None
    parameters: list[
        tuple[jack_scanner.Token, jack_scanner.Token, jack_scanner.Token]
    ] = dataclasses.field(default_factory=list)

    @property
    def variables(self) -> list[ParameterVar]:
        """
        Returns the variables as a list of tuples.
        TODO: this should return a list of ParameterVar
        """
        parameters: list[ParameterVar] = []
        if self._type is None or self.varname is None:
            return parameters  # this must mean that subroutine has no arguments

        parameters.append(
            ParameterVar(type_=self._type.lexeme, varname=self.varname.lexeme)
        )

        for parameter in self.parameters:
            type_ = parameter[1].lexeme
            varname = parameter[2].lexeme
            parameters.append(ParameterVar(type_=type_, varname=varname))
        return parameters

    @property
    def number_of_arguments(self):
        return len(self.variables)

    def write_xml(self, file: typing.IO, indent: int = 0):
        self.eval_node()
        self.write_eval(file)
        with self.write_node(file, indent) as t:
            if self._type is None or self.varname is None:
                # self.write_node(file, indent, is_opening_tag=False)
                return
            indent += 2
            self.write_token(self._type, file, indent)
            self.write_token(self.varname, file, indent)
            for comma, next_type, next_varname in self.parameters:
                self.write_token(comma, file, indent)
                self.write_token(next_type, file, indent)
                self.write_token(next_varname, file, indent)
            # self.write_node(file, indent, is_opening_tag=False)

    def eval_node(self, file: typing.IO):
        LOGGER.debug("eval:ParameterList")
        if current_class_name is None:
            raise Exception(
                f"can't set 'this' of {current_subroutine_name}, because current class name is None"
            )
        subroutine_symbols["this"] = VariableInfo(
            type_=current_class_name, kind="argument", occurrence=0
        )
        for type_, varname in self.variables:
            # if no varname then error
            field_type_count = subroutine_occurrences["argument"]

            LOGGER.info(
                "subroutine_symbol: %s -> [%s, %s, %s]"
                % (
                    varname,
                    type_,
                    "argument",
                    field_type_count,
                )
            )
            # type, kind, occurrence
            subroutine_symbols[varname] = VariableInfo(
                type_=type_,
                kind="argument",
                occurrence=field_type_count,
            )
            subroutine_occurrences["argument"] = field_type_count + 1

    def write_eval(self, file: typing.IO):
        for type_, varname in self.variables:
            surround = "paramListSymbols"
            var_info = subroutine_symbols[varname]
            LOGGER.debug(f"writing {varname} to file")
            file.write(f"""
    {" " * indent}<{surround}> 
        name: {varname}
        category: {var_info.kind}
        index: {var_info.occurrence}
        usage: parameter list
    {" " * indent}</{surround}>\n
            """)


class VarDecSymbols(typing.NamedTuple):
    type_: str
    var_name: str


@dataclasses.dataclass
class VarDec(XmlWriter):
    var_kw: jack_scanner.Token
    _type: jack_scanner.Token
    var_name: jack_scanner.Token
    var_names: list[tuple[jack_scanner.Token, jack_scanner.Token]]
    semi_colon: jack_scanner.Token

    @property
    def symbol_names(self) -> list[VarDecSymbols]:
        var_names = [
            VarDecSymbols(type_=self._type.lexeme, var_name=self.var_name.lexeme)
        ]

        # pretty sure this is wrong - type_ here is not the type, but instead a comma
        for _, var_name in self.var_names:
            var_names.append(
                VarDecSymbols(type_=self._type.lexeme, var_name=var_name.lexeme)
            )

        return var_names

    def write_xml(self, file: typing.IO, indent: int):
        self.eval_node()
        self.write_eval(file)
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.var_kw, file, indent)
            self.write_token(self._type, file, indent)
            self.write_token(self.var_name, file, indent)
            for comma, var_name in self.var_names:
                self.write_token(comma, file, indent)
                self.write_token(var_name, file, indent)
            self.write_token(self.semi_colon, file, indent)

    def eval_node(self, file: typing.IO):
        LOGGER.debug("eval:VarDec")
        for type_, symbol in self.symbol_names:
            field_type_count = subroutine_occurrences["local"]
            LOGGER.debug(
                "[VarDec]subroutine_symbol: %s -> [%s, %s, %s]"
                % (
                    symbol,
                    type_,
                    "local",
                    field_type_count,
                )
            )
            # these have to be local right???
            subroutine_symbols[symbol] = VariableInfo(
                type_=type_, kind="local", occurrence=field_type_count
            )
            subroutine_occurrences["local"] = field_type_count + 1

    def write_eval(self, file: typing.IO):
        surround = "VarDecSymbol"
        for type_, symbol in self.symbol_names:
            var_info = subroutine_symbols[symbol]
            file.write(f"""
        {" " * indent}<{surround}> 
            name: {symbol}
            category: {var_info.kind}
            index: {var_info.occurrence}
            usage: Class Variables Declaration
        {" " * indent}</{surround}>\n
                """)


@dataclasses.dataclass
class SubroutineBody(XmlWriter, ASTEval):
    left_squerly: jack_scanner.Token
    var_decs: list[VarDec]
    statements: Statements
    right_squerly: jack_scanner.Token

    @property
    def variable_declaration_count(self):
        return sum([len(var_dec.symbol_names) for var_dec in self.var_decs])

    def write_xml(self, file: typing.IO, indent: int):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.left_squerly, file, indent)
            for var_dec in self.var_decs:
                var_dec.write_xml(file, indent)
            self.statements.write_xml(file, indent)
            self.write_token(self.right_squerly, file, indent)

    def eval_node(self, file: typing.IO):
        LOGGER.debug("eval:SubroutineBody")

        for var_dec in self.var_decs:
            var_dec.eval_node(file)

        # there seems to be a bug with my parser, because the jack program
        # isn't working
        LOGGER.debug(f"eval:Statment?? {len(self.statements.statements)}")
        for statement in self.statements.statements:
            LOGGER.debug("eval:Statment??")
            statement.eval_node(file)


@dataclasses.dataclass
class Expression(XmlWriter, ASTEval):
    term: Term
    op_terms: list[tuple[jack_scanner.Token, Term]]

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.term.write_xml(file, indent)
            for op, term in self.op_terms:
                self.write_token(op, file, indent)
                term.write_xml(file, indent)

    def eval_node(self, file: typing.IO):
        indent = get_code_gen_indent() * " "
        LOGGER.debug("eval:Expression")
        self.term.eval_node(file)
        if op_term := next(iter(self.op_terms), None):
            operator, operand = op_term
            operand.eval_node(file)
            LOGGER.debug(f"eval:Expression:op_term:'{operator.lexeme}'")
            LOGGER.debug(f"write:'{operator.lexeme}'")
            match operator.lexeme:
                case "+":
                    file.write(indent + "add\n")
                case "-":
                    file.write(indent + "sub\n")
                case "*":
                    # x + y
                    # file.write("pop temp 0") # y top most thing on stack
                    # file.write("pop temp 1") # x next top most thing
                    file.write(indent + "call Math.multiply 2\n")
                case ">":
                    file.write(indent + "gt\n")
                case "<":
                    file.write(indent + "lt\n")
                case "=":
                    # i'm not totally sure this is the equal operator in jack?
                    file.write(indent + "eq\n")
                case "&":
                    file.write(indent + "and\n")
                case _:
                    raise Exception(
                        f"operator: '{operator.lexeme}' is not a valid operator"
                    )

    # def write_eval(self, file: typing.IO):
    #     return super().write_eval(file)


@dataclasses.dataclass
class Term(XmlWriter, ASTEval):
    term: (
        jack_scanner.Token
        | tuple[jack_scanner.Token, Term]
        | tuple[jack_scanner.Token, Expression, jack_scanner.Token]
        | tuple[jack_scanner.Token, jack_scanner.Token, Expression, jack_scanner.Token]
        | SubroutineCall
    )

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            match self.term:
                case jack_scanner.Token():
                    self.write_token(self.term, file, indent)
                case (token, term):
                    self.write_token(token, file, indent)
                    term.write_xml(file, indent)
                case (token, expression, token_end):
                    self.write_token(token, file, indent)
                    expression.write_xml(file, indent)
                    self.write_token(token_end, file, indent)
                case (token, token_two, expression, token_end):
                    self.write_token(token, file, indent)
                    self.write_token(token_two, file, indent)
                    expression.write_xml(file, indent)
                    self.write_token(token_end, file, indent)
                case SubroutineCall():
                    self.term.write_xml(file, indent)

    def eval_node(self, file: typing.IO):
        LOGGER.debug("eval:Term")
        self.write_eval(file)

    def write_eval(self, file: typing.IO):
        indent = get_code_gen_indent() * " "
        vm_code_stream = ""
        match self.term:
            case jack_scanner.Token() as token:
                # integer / string / keyword constant
                match self.term.token_type:
                    case jack_scanner.TokenType.INTEGER_CONSTANT:
                        vm_code_stream = f"push constant {self.term.lexeme}\n"
                        file.write(indent + vm_code_stream)
                        return vm_code_stream
                    case jack_scanner.TokenType.IDENTIFIER:
                        # this is an identifier so it must be in my symbol table right - first check
                        # the subroutine level symbol table then the class level one
                        symbol = token.lexeme
                        match subroutine_symbols.get(symbol, None) or class_symbols.get(
                            symbol, None
                        ):
                            case VariableInfo(type_, kind, occurrences):
                                # this will only work for really simple expressions right now
                                file.write(indent + f"push {kind} {occurrences} \n")
                            case _:
                                # if symbol is None:
                                raise Exception(f"{symbol} not defined")
                    case boolean_token if boolean_token in jack_scanner.booleans:
                        if token.token_type == jack_scanner.TokenType.TRUE:
                            file.write(indent + "push constant 1\n")
                            file.write(indent + "neg\n")
                        else:
                            file.write(indent + "push constant 0\n")
                    case _:
                        raise Exception(
                            "issue evaluating Term: %(lexeme)s %(token_type)s"
                            % {
                                "lexeme": token.lexeme,
                                "token_type": token.token_type.name,
                            }
                        )
            case (token, term):
                LOGGER.debug(f"eval:(UnaryOp term) {token.lexeme}")
                term.eval_node(file)
                if token.token_type == jack_scanner.TokenType.TILDE:
                    file.write(indent + "not\n")
                else:
                    file.write(indent + "neg\n")
            case (_open_paren, expression, _close_paren):
                # ( expression )
                expression.eval_node(file)
            case (var_name, left_square_bracket, expression, right_square_bracket):
                # varName [ expression ]
                expression.eval_node(file)
                # do something with token???
            case SubroutineCall():
                self.term.eval_node(file)


@dataclasses.dataclass
class ExpressionList(XmlWriter, ASTEval):
    expression: Expression | None = None
    expression_list: list[tuple[jack_scanner.Token, Expression]] | None = None

    @property
    def num_expression(self):
        return 1 + len(self.expression_list or [])

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            if self.expression:
                self.expression.write_xml(file, indent)
                if self.expression_list:
                    for comma, expr in self.expression_list:
                        self.write_token(comma, file, indent)
                        expr.write_xml(file, indent)

    def eval_node(self, file: typing.IO):
        if self.expression:
            self.expression.eval_node(file)
            for expr in self.expression_list or []:
                expr[1].eval_node(file)

    def write_eval(self, file: typing.IO):
        return super().write_eval(file)


@dataclasses.dataclass
class SubroutineCall(XmlWriter, ASTEval):
    subroutine_name: jack_scanner.Token
    left_paren: jack_scanner.Token
    right_paren: jack_scanner.Token
    dot: jack_scanner.Token | None = None
    subroutine_source: jack_scanner.Token | None = None
    expression_list: ExpressionList = dataclasses.field(
        default_factory=lambda: ExpressionList()
    )

    def write_xml(self, file: typing.IO, indent: int = 0):
        if self.subroutine_source:
            self.write_token(self.subroutine_source, file, indent)
            self.write_token(self.dot, file, indent)
        self.write_token(self.subroutine_name, file, indent)
        self.write_token(self.left_paren, file, indent)
        self.expression_list.write_xml(file, indent)
        self.write_token(self.right_paren, file, indent)

    def eval_node(self, file: typing.IO):
        self.expression_list.eval_node(file)
        self.write_eval(file)

    def write_eval(self, file: typing.IO):
        indent = get_code_gen_indent() * " "
        if (
            self.subroutine_source
        ):  # assuming subroutine_source is a basically a className
            file.writelines([
                indent
                + f"call {self.subroutine_source.lexeme}.{self.subroutine_name.lexeme} {self.expression_list.num_expression}\n"
            ])


type StatementType = (
    LetStatement | IfStatement | WhileStatement | DoStatement | ReturnStatement
)


@dataclasses.dataclass
class Statements(XmlWriter, ASTEval):
    statements: list[StatementType]

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            for statement in self.statements:
                statement.write_xml(file, indent)

    def eval_node(self, file: typing.IO):
        # note: doesn't do anything with write_eval
        for statement in self.statements:
            statement.eval_node(file)


@dataclasses.dataclass
class ReturnStatement(XmlWriter, ASTEval):
    return_kw: jack_scanner.Token
    semicolon: jack_scanner.Token
    expression: Expression | None = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.return_kw, file, indent)
            if self.expression:
                self.expression.write_xml(file, indent)
            self.write_token(self.semicolon, file, indent)

    def eval_node(self, file: typing.IO):
        self.write_eval(file)

    def write_eval(self, file: typing.IO):
        indent = get_code_gen_indent() * " "
        if self.expression:
            self.expression.eval_node(file)
        else:
            file.write(indent + "push constant 0\n")
        file.write(indent + "return\n")


@dataclasses.dataclass
class DoStatement(XmlWriter, ASTEval):
    do_kw: jack_scanner.Token
    subroutine_call: SubroutineCall
    semicolon: jack_scanner.Token

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.do_kw, file, indent)
            self.subroutine_call.write_xml(file, indent)
            self.write_token(self.semicolon, file, indent)

    def eval_node(self, file: typing.IO):
        self.subroutine_call.eval_node(file)

    def write_eval(self, file: typing.IO):
        pass


@dataclasses.dataclass
class LetStatement(XmlWriter, ASTEval):
    let_kw: jack_scanner.Token
    var_name: jack_scanner.Token
    equal: jack_scanner.Token
    expression: Expression
    semi_colon: jack_scanner.Token
    index_var: tuple[jack_scanner.Token, Expression, jack_scanner.Token] | None = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.let_kw, file, indent)
            self.write_token(self.var_name, file, indent)
            if self.index_var:
                left_square, expression, right_square = self.index_var
                self.write_token(left_square, file, indent)
                expression.write_xml(file, indent)
                self.write_token(right_square, file, indent)
            self.write_token(self.equal, file, indent)
            self.expression.write_xml(file, indent)
            self.write_token(self.semi_colon, file, indent)

    def eval_node(self, file: typing.IO):
        LOGGER.debug("eval:LetStatement")
        self.expression.eval_node(file)
        self.write_eval(file)

    def write_eval(self, file: typing.IO):
        indent = get_code_gen_indent()
        symbol = self.var_name.lexeme
        var_info = subroutine_symbols.get(symbol, None)
        if var_info is None:
            raise Exception(f"{symbol} does not exist in subroutine level symbol table")
        file.write(
            f"{indent * " "}pop {var_info.kind} {var_info.occurrence}\n"
        )  # pop top of stack and put it into segment[i]


if_statement_instance = 0


@dataclasses.dataclass
class IfStatement(XmlWriter, ASTEval):
    if_kw: jack_scanner.Token
    left_paren: jack_scanner.Token
    expression: Expression
    right_paren: jack_scanner.Token
    left_curly: jack_scanner.Token
    right_curly: jack_scanner.Token
    statements: Statements
    optional_else: (
        tuple[jack_scanner.Token, jack_scanner.Token, Statements, jack_scanner.Token]
        | None
    ) = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.if_kw, file, indent)
            self.write_token(self.left_paren, file, indent)
            self.expression.write_xml(file, indent)
            self.write_token(self.right_paren, file, indent)
            self.write_token(self.left_curly, file, indent)
            self.statements.write_xml(file, indent)
            self.write_token(self.right_curly, file, indent)
            if self.optional_else:
                else_kw, left_curly, statements, right_curly = self.optional_else
                self.write_token(else_kw, file, indent)
                self.write_token(left_curly, file, indent)
                statements.write_xml(file, indent)
                self.write_token(right_curly, file, indent)

    def eval_node(self, file: typing.IO):
        self.write_eval(file)

    def write_eval(self, file: typing.IO):
        indent = get_code_gen_indent() * " "
        global if_statement_instance
        if_statement_instance += 3
        L1 = f"L{if_statement_instance - 2}"
        L2 = f"L{if_statement_instance - 1}"

        self.expression.eval_node(file)
        file.write(indent + "not\n")
        file.write(indent + f"if-goto {L1}\n")
        self.statements.eval_node(file)
        file.write(indent + f"goto {L2}\n")
        file.write(indent + f"label {L1}\n")
        if else_clause := self.optional_else:
            else_clause[2].eval_node(file)
        file.write(indent + f"label {L2}\n")


while_loop_instance = 0


@dataclasses.dataclass
class WhileStatement(XmlWriter, ASTEval):
    while_kw: jack_scanner.Token
    left_paren: jack_scanner.Token
    expression: Expression
    right_paren: jack_scanner.Token
    left_curly: jack_scanner.Token
    right_curly: jack_scanner.Token
    statements: Statements

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.while_kw, file, indent)
            self.write_token(self.left_paren, file, indent)
            self.expression.write_xml(file, indent)
            self.write_token(self.right_paren, file, indent)
            self.write_token(self.left_curly, file, indent)
            self.statements.write_xml(file, indent)
            self.write_token(self.right_curly, file, indent)

    def eval_node(self, file: typing.IO):
        self.write_eval(file)

    def write_eval(self, file: typing.IO):
        indent = get_code_gen_indent() * " "

        global while_loop_instance
        while_loop_instance += 1
        # evaluate the expression. It's now on top of the stack
        # while_loop_instance = f"WHILE_LOOP"
        file.write(indent + f"label WHILE_LOOP{while_loop_instance}\n")
        self.expression.eval_node(file)
        file.write(indent + "not\n")
        file.write(indent + f"if-goto WHILE_LOOP{while_loop_instance}Complete\n")
        self.statements.eval_node(file)
        file.write(indent + f"goto WHILE_LOOP{while_loop_instance}\n")
        file.write(indent + f"label WHILE_LOOP{while_loop_instance}Complete\n")
