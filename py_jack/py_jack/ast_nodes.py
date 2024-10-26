from __future__ import annotations
import py_jack.jack_scanner as jack_scanner
import pathlib
import typing
import dataclasses
import contextlib
import logging


LOGGER: typing.Final = logging.getLogger(__name__)


class AbstractExpression(typing.Protocol):
    pass

class CodeGenWriter[T: typing.IO]:
    """
    this is one way to implement code indentation
    """
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

@dataclasses.dataclass
class CurrentSubroutine:
    variant: str
    name: str
    type_: str

class_symbols: dict[str, VariableInfo] = {}
current_subroutine_name: CurrentSubroutine | None = None
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


class SymbolInfo(typing.NamedTuple):
    is_class_level: bool
    var_info: VariableInfo

def get_symbol_info(symbol: str) -> SymbolInfo:

    is_class_level = symbol in class_symbols
    var_info = class_symbols.get(symbol) or subroutine_symbols.get(symbol) # not really sure what to do if there are duplicates
    if var_info is None:
        raise Exception(f"'{symbol}' does not exist")

    
    return SymbolInfo(is_class_level=is_class_level, var_info=var_info)



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
        """
        TODO: need to change this. I'm basically using this as the entry point into to reset the symbol
        tables. There's definitely a more buttoned up way to do this than this.
        """
        # assumes file is valid at least and will create it
        LOGGER.info(f"writing to: {file.resolve()}")

        global class_occurrences
        global class_symbols
        global current_class_name
        global current_subroutine_name

        class_occurrences = {
            "field": 0,
            "static": 0,
            "local": 0,
            "argument": 0,
            # there are more of these just not really sure about them
        }
        class_symbols = {}
        current_class_name = None
        current_subroutine_name = None

        mode = "w"
        with file.open(mode) as vm_code_file:
            self.eval_node(file=vm_code_file)

    def eval_node(self, file: typing.IO):
        LOGGER.debug("eval:ClassNode")
        global current_class_name
        current_class_name = self.class_name.lexeme
        LOGGER.debug(f"current_class_name set to: {current_class_name}")

        for class_var_def in self.class_var_dec or []:
            class_var_def.eval_node(file)

        for subroutine_dec in self.subroutine_dec or []:
            subroutine_dec.eval_node(file)



class ClassVariable(typing.NamedTuple):

    type_: str
    var_names: list[str]

@dataclasses.dataclass
class ClassVarDec(XmlWriter, ASTEval):
    field_type: jack_scanner.Token
    type_: jack_scanner.Token
    var_name: jack_scanner.Token
    semi_colon: jack_scanner.Token
    var_names: list[tuple[jack_scanner.Token, jack_scanner.Token]] | None = None


    @property
    def class_vars(self) -> ClassVariable:
        var_names = []
        var_names.append(self.var_name.lexeme)

        for _comma, identifier in self.var_names:
            var_names.append(identifier.lexeme)

        return ClassVariable(
                    type_=self.type_.lexeme,
                    var_names=var_names
                    )

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
        type_, vnames = self.class_vars
        for var_name in vnames:
            field_type_count = class_occurrences[self.field_type.lexeme]
            LOGGER.debug(
                "add class-level symbol: %s -> [%s, %s, %s]"
                % (
                    var_name,
                    type_,
                    self.field_type.lexeme,
                    field_type_count,
                )
            )
            # type, kind, occurrence
            class_symbols[var_name] = VariableInfo(
                type_=type_,
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
            current_subroutine_name = CurrentSubroutine(name= self.name.lexeme, variant=self.subroutine_variant.lexeme, type_=self.return_type.lexeme)

            global subroutine_symbols
            subroutine_symbols = {}
            reset_subroutine_occurrences()
            LOGGER.info(f"compiling subroutine: {current_subroutine_name.name}")
            self.write_eval(file)

    def write_eval(self, file: typing.IO):
        LOGGER.debug("write:SubroutineDec")
        global current_class_name
        global current_subroutine_name
        global current_class_name
        global subroutine_occurrences
        indent = get_code_gen_indent()
        match self.subroutine_variant.token_type:
            case jack_scanner.TokenType.CONSTRUCTOR:
                if current_class_name is None:
                    raise Exception("current_class_name is not defined")

                # TODO: does this exist in the constuctor? I mean it must - why wouldn't you be able to refer
                # to other functions / methods inside the constructor if you wanted to?
                subroutine_symbols["this"] = VariableInfo(
                    type_=current_class_name, kind="argument", occurrence=0
                )
                # subroutine_occurrences["argument"] += 1

                LOGGER.info(f"subroutine_occurrences before parameter_list eval: {subroutine_occurrences}")

                self.parameter_list.eval_node(file)

                local_argument_count = (
                    self.subroutine_body.variable_declaration_count
                )

                file.write(
                    f"function {current_class_name}.{current_subroutine_name.name} {local_argument_count}\n"
                )

                LOGGER.info(f"current class level symbols: {class_symbols}")
                file.write(f"{indent * ' '}push constant {len([symbol
                                                               for symbol, symbol_info in class_symbols.items()
                                                               if symbol_info.kind == "field"])}\n") # class_symbols should be equal to how much space we need for this object
                file.write(f"{indent * ' '}call Memory.alloc 1\n")
                file.write(f"{indent * ' '}pop pointer 0\n")
                self.subroutine_body.eval_node(file)

            case jack_scanner.TokenType.METHOD:
                if current_class_name is None:
                    raise Exception("current_class_name is not defined")
                subroutine_symbols["this"] = VariableInfo(
                    type_=current_class_name, kind="argument", occurrence=0
                )
                subroutine_occurrences["argument"] += 1
                self.parameter_list.eval_node(file)
                local_argument_count = (
                    self.subroutine_body.variable_declaration_count
                )  # arguments to a function are not considered local variables
                file.write(
                    f"function {current_class_name}.{current_subroutine_name.name} {local_argument_count}\n"
                )
                file.write(f"{indent * " "}push argument 0\n")
                file.write(f"{indent * " "}pop pointer 0\n") # set the this pointer of the method
                self.subroutine_body.eval_node(file)
            case jack_scanner.TokenType.FUNCTION:
                self.parameter_list.eval_node(file)

                local_argument_count = (
                    self.subroutine_body.variable_declaration_count
                )  # arguments to a function are not considered local variables

                file.write(
                    f"function {current_class_name}.{current_subroutine_name.name} {local_argument_count}\n"
                )
                self.subroutine_body.eval_node(file)
            case _:
                raise Exception(f"subroutine type {self.subroutine_variant.lexeme} is not one of: constructor, function, or method.")



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
                f"can't set 'this' of {current_subroutine_name.name}, because current class name is None"
            )
        for type_, varname in self.variables:
            # if no varname then error
            global subroutine_occurrences
            field_type_count = subroutine_occurrences["argument"]

            LOGGER.info(f"subroutine_occurrences: {subroutine_occurrences}")
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

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.left_squerly, file, indent)
            for var_dec in self.var_decs:
                var_dec.write_xml(file, indent)
            self.statements.write_xml(file, indent)
            self.write_token(self.right_squerly, file, indent)

    def eval_node(self, file: typing.IO):
        LOGGER.debug(f"eval:SubroutineBody")
        for var_dec in self.var_decs:
            var_dec.eval_node(file)
        for statement in self.statements.statements:
            statement.eval_node(file)



@dataclasses.dataclass
class Expression(AbstractExpression ,XmlWriter, ASTEval):
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
                case "/":
                    file.write(indent + "call Math.divide 2\n")
                case ">":
                    file.write(indent + "gt\n")
                case "<":
                    file.write(indent + "lt\n")
                case "=":
                    # i'm not totally sure this is the equal operator in jack?
                    file.write(indent + "eq\n")
                case "&":
                    file.write(indent + "and\n")
                case "|":
                    file.write(indent + "or\n")
                case _:
                    raise Exception(
                        f"operator: '{operator.lexeme}' is not a valid operator"
                    )



def push_string(indent: str, string_constant: str, file: typing.IO):
    file.write(indent + f"push constant {len(string_constant)}\n")
    file.write(indent + f"call String.new 1\n")
    for char in string_constant:
        file.write(indent + f"push constant {ord(char)}\n")
        file.write(indent + f"call String.appendChar 2\n")







@dataclasses.dataclass
class Term(AbstractExpression, XmlWriter, ASTEval):
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
                    case jack_scanner.TokenType.STRING_CONSTANT:
                        push_string(indent, token.lexeme, file)
                    case jack_scanner.TokenType.IDENTIFIER | jack_scanner.TokenType.THIS:
                        """
                        If you're accessing a local variable then you're getting things from the local segment,
                        but if you're accessing an identifier from the class level sybmol table then you need to
                        get it from the 'this' location in memory
                        """
                        
                        # this is an identifier so it must be in my symbol table right - first check
                        # the subroutine level symbol table then the class level one
                        symbol = token.lexeme
                        if symbol == "this":
                            file.write(indent+ f"push pointer 0\n") # if symbol is this then you always want to do this
                            return
                        is_valid_symbol = (class_symbols.get(symbol, None) or subroutine_symbols.get(symbol, None)) is not None
                        is_class_level_symbol = class_symbols.get(symbol, None) is not None

                        if not is_valid_symbol:
                            raise Exception(f"{symbol} does not exist.")

                        symbol_info = class_symbols.get(symbol, None) or subroutine_symbols.get(symbol, None)

                        match symbol_info:
                            case VariableInfo(type_, kind, occurrences):
                                # this will only work for really simple expressions right now
                                if is_class_level_symbol:
                                    """
                                    NOTE: stopped here - basically I need to make sure that static variables will work how I think
                                    they'll work and then we should be good.
                                    """ 
                                    if symbol_info.kind == "static":
                                        file.write(indent + f"push static {occurrences}\n")
                                    else:
                                        # it must be field - field and static are the only options
                                        file.write(indent + f"push this {occurrences}\n")
                                else:
                                    file.write(indent + f"push {kind} {occurrences}\n")
                            case _:
                                # if symbol is None:
                                raise Exception(f"{symbol} not defined")
                    case boolean_token if boolean_token in jack_scanner.booleans:
                        if token.token_type == jack_scanner.TokenType.TRUE:
                            file.write(indent + "push constant 1\n")
                            file.write(indent + "neg\n")
                        else:
                            file.write(indent + "push constant 0\n")
                    case jack_scanner.TokenType.NULL:
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
                is_class_level, var_info = get_symbol_info(var_name.lexeme)
                if is_class_level:
                    file.write(indent + f"push this {var_info.occurrence}\n")
                else:
                    file.write(indent + f"push {var_info.kind} {var_info.occurrence}\n")
                file.write(indent + "add\n")
                file.write(indent + "pop pointer 1\n")
                file.write(indent + "push that 0\n")
            case SubroutineCall():
                self.term.eval_node(file)


@dataclasses.dataclass
class ExpressionList(XmlWriter, ASTEval):
    expression: Expression | None = None
    expression_list: list[tuple[jack_scanner.Token, Expression]] | None = None

    @property
    def num_expression(self):
        return (1 if self.expression else 0) + len(self.expression_list or [])

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

#    def write_eval(self, file: typing.IO):
#        return super().write_eval(file)


@dataclasses.dataclass
class SubroutineCall(AbstractExpression, XmlWriter, ASTEval):
    """
    calls like:
        - do something();
        - do Square.draw(); 
    calls like the above can return a value or be void

    the above is not true - in a do statement you can always just pop the value off because it will
    never be used. But in a let statement it might be used.
    """
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
        LOGGER.debug("eval:SubroutineCall")
        self.write_eval(file)

    def write_eval(self, file: typing.IO):
        indent = get_code_gen_indent() * " "
        # this is the issue - I'm assuming there is always a subroutine source, but this is not the case - draw is a method
        # so I can't just do `call draw x` it needs to be `Square.draw`, but how do I know if that 
        # for now I can just put the class name, but I need to be able to distinguish 
        if (
            self.subroutine_source
        ):  # assuming subroutine_source is a basically a className 

            """
            when you do a subroutine call what can it be

            1. it can be a method call - in which case you are calling a method on the current object
            2. it can be a function call - you are calling a function in some other object?
            """

            symbol = self.subroutine_source.lexeme

            if symbol not in class_symbols and symbol not in subroutine_symbols:
                LOGGER.warn(f"'{symbol}' does not exist. Assuming call to external class.")
                self.expression_list.eval_node(file)
                file.writelines([
                    indent
                    + f"call {self.subroutine_source.lexeme}.{self.subroutine_name.lexeme} {self.expression_list.num_expression}\n"
                ])
                return 

            is_class_level = self.subroutine_source.lexeme in class_symbols
            var_info = None
            if symbol in class_symbols:
                var_info = class_symbols[self.subroutine_source.lexeme]
            else:
                var_info = subroutine_symbols[self.subroutine_source.lexeme]

            if is_class_level:
                file.write(f"{indent}push this {var_info.occurrence}\n")
                self.expression_list.eval_node(file)
                file.writelines([
                    indent
                    + f"call {var_info.type_}.{self.subroutine_name.lexeme} {self.expression_list.num_expression + 1}\n"
                ])
                LOGGER.debug(f"wrote: push this {var_info.occurrence}\n") 
                LOGGER.debug(f"wrote: call {var_info.type_}.{self.subroutine_name.lexeme} {self.expression_list.num_expression}")
            else:
                file.write(indent + f"push {var_info.kind} {var_info.occurrence}\n")
                self.expression_list.eval_node(file)
                file.writelines([
                    indent
                    + f"call {var_info.type_}.{self.subroutine_name.lexeme} {self.expression_list.num_expression + 1}\n" 
                ])
                LOGGER.debug(f"wrote: call {var_info.type_}.{self.subroutine_name.lexeme} {self.expression_list.num_expression}")

        else:
            # this syntax is for methods only - although I don't see why you couldn't also use the above for
            # method calls
            file.write(f"{indent}push pointer 0\n")
            self.expression_list.eval_node(file)
            # add + 1 to expression_list because this is always a method call
            file.writelines([
                indent
                + f"call {current_class_name}.{self.subroutine_name.lexeme} {self.expression_list.num_expression + 1} \n"
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

        if current_subroutine_name.variant == "constructor":
            file.write(indent + "push pointer 0\n")
            file.write(indent + "return\n")
            return


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
        indent = get_code_gen_indent() * " "
        self.subroutine_call.eval_node(file)
        file.write(indent + "pop temp 0\n")

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
        indent = get_code_gen_indent() * " "
        if self.index_var:
            index_var_expression = self.index_var[1]
            index_var_expression.eval_node(file)
            is_class_level, var_info = get_symbol_info(self.var_name.lexeme)
            if is_class_level:
                file.write(indent + f"push this {var_info.occurrence}\n")
            else:
                file.write(indent + f"push {var_info.kind} {var_info.occurrence}\n")
            file.write(indent + "add\n")
            self.expression.eval_node(file)
            file.write(indent + "pop temp 0\n")
            file.write(indent + "pop pointer 1\n")
            file.write(indent + "push temp 0\n")
            file.write(indent + "pop that 0\n")
        else:
            self.expression.eval_node(file)
            self.write_eval(file)

    def write_eval(self, file: typing.IO):
        indent = get_code_gen_indent()
        symbol = self.var_name.lexeme
        var_info = None 
        if symbol in class_symbols:
            var_info = class_symbols.get(symbol, None)
        elif symbol in subroutine_symbols:
            LOGGER.info(f"{symbol} not in class level symbol table")
            var_info = subroutine_symbols.get(symbol, None)
        if var_info is None:
            LOGGER.debug(class_symbols)
            LOGGER.debug(subroutine_symbols)
            raise Exception(f"{symbol} does not exist in symbol tables")

        if var_info.kind == "field":
            file.write(
                f"{indent * " "}pop this {var_info.occurrence}\n"
            )  # pop top of stack and put it into segment[i]
        else:
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
        L1 = f"LL{if_statement_instance - 2}"
        L2 = f"LL{if_statement_instance - 1}"

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
        current_while_loop_instance = while_loop_instance 
        LOGGER.debug(f"while loop instance: {while_loop_instance}")
        

        # evaluate the expression. It's now on top of the stack
        # while_loop_instance = f"WHILE_LOOP"
        file.write(indent + f"label WHILE_LOOP{current_while_loop_instance}\n")
        self.expression.eval_node(file)
        file.write(indent + "not\n")
        file.write(indent + f"if-goto WHILE_LOOP{current_while_loop_instance}Complete\n")
        self.statements.eval_node(file)
        file.write(indent + f"goto WHILE_LOOP{current_while_loop_instance}\n")
        file.write(indent + f"label WHILE_LOOP{current_while_loop_instance}Complete\n")
