import py_jack.scanner as jack_scanner
import py_jack.parser as jack_parser
import py_jack.ast_nodes as jack_ast

valid_programs = {
    "subroutineDec": """
    function void main() {
        var SquareGame game;
        let game = game;
        do game.run();
        do game.dispose();
        return;
    }
    """,
}


def test_class_var_dec():
    """
    TODO: figure out how to test this better. This is a good isolated test case for this rule.
    just need to figure out how I can easily read in things to test this against
    """

    scanner = jack_scanner.Scanner(src="static boolean test;")
    scanner.scan()

    parser = jack_parser.Parser(tokens=scanner.tokens)

    class_var_dec = parser.parse_class_var_dec()  # should not fail
    # n.write_xml(file=sys.stdout, indent=0)
    assert class_var_dec.field_type.lexeme == "static"
    assert class_var_dec.type_.lexeme == "boolean"
    assert class_var_dec.var_name.lexeme == "test"
    assert len(class_var_dec.var_names) == 0
    assert class_var_dec.semi_colon.lexeme == ";"


# TODO: was going to parse subRoutineDec, but that requires all statements, so going to do that first
def test_parameter_list():
    # int myInt, char myChar, "Square mySquare"
    src = "int myInt, char myChar, Square mySquare"

    scanner = jack_scanner.Scanner(src)
    scanner.scan()

    token_iter = iter(scanner.tokens)

    assert next(token_iter).lexeme == "int"
    assert next(token_iter).lexeme == "myInt"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "char"
    assert next(token_iter).lexeme == "myChar"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "Square"
    assert next(token_iter).lexeme == "mySquare"
    assert next(token_iter, None) is None

    parser = jack_parser.Parser(tokens=scanner.tokens)
    parameter_list = parser.parse_parameter_list()

    def map_lexemes(pl):
        return (pl[0].lexeme, pl[1].lexeme, pl[2].lexeme)

    assert len(parameter_list.parameters) == 2

    parameters = iter(parameter_list.parameters)

    assert (parameter_list._type.lexeme, parameter_list.varname.lexeme) == (
        "int",
        "myInt",
    )
    assert map_lexemes(next(parameters)) == (",", "char", "myChar")
    assert map_lexemes(next(parameters)) == (",", "Square", "mySquare")


def test_simple_scan():
    scanner = jack_scanner.Scanner(src="char myChar, Square mySquare")
    scanner.scan()

    token_iter = iter(scanner.tokens)

    assert next(token_iter).lexeme == "char"


def test_subroutine_call():
    src = """
    method void dispose() {
      do square.dispose();
      do Memory.deAlloc(this);
      return;
    }
    """

    scanner = jack_scanner.Scanner(src=src)
    scanner.scan()

    parser = jack_parser.Parser(scanner.tokens)

    subroutine = parser.subroutine_dec()

    assert isinstance(subroutine, jack_ast.SubroutineDec)
    assert subroutine.name.lexeme == "dispose"
    assert subroutine.subroutine_variant.lexeme == "method"
    assert len(subroutine.subroutine_body.var_decs) == 0
    assert len(subroutine.subroutine_body.statements) == 3


def test_var_decs():
    src = """
    function void main() {
        var SquareGame game;
        var char name;
        return;
    }
    """

    scanner = jack_scanner.Scanner(src=src)
    scanner.scan()

    parser = jack_parser.Parser(scanner.tokens)

    subroutine = parser.subroutine_dec()

    assert isinstance(subroutine, jack_ast.SubroutineDec)
    assert subroutine.name.lexeme == "main"
    assert subroutine.subroutine_variant.lexeme == "function"
    assert len(subroutine.subroutine_body.var_decs) == 2
    assert len(subroutine.subroutine_body.statements) == 1


def test_basic_program():
    src = """
    class Main {
        static boolean test;    // Added for testing -- there is no static keyword
                                // in the Square files.
        function void main() {
            var SquareGame game;
            let game = SquareGame.new();
            do game.run();
            do game.dispose();
            return;
        }

        function void more() {  // Added to test Jack syntax that is not used in
            var int i, j;       // the Square files.
            var String s;
            var Array a;
            if (false) {
                let s = "string constant";
                let s = null;
                let a[1] = a[2];
            }
            else {              // There is no else keyword in the Square files.
                let i = i * (-j);
                let j = j / (-2);   // note: unary negate constant 2
                let i = i | j;
            }
            return;
        }
    }
    """

    scanner = jack_scanner.Scanner(src=src)
    scanner.scan()

    parser = jack_parser.Parser(scanner.tokens)

    prg = parser.parse_class()

    assert isinstance(prg, jack_ast.ClassNode)
    assert prg.class_name.lexeme == "Main"
    assert prg.class_var_dec is not None
    assert len(prg.class_var_dec) == 1
    assert prg.subroutine_dec is not None
    assert len(prg.subroutine_dec) == 2
