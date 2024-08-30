import py_jack.scanner as jack_scanner
import py_jack.parser as jack_parser
import py_jack.ast as jack_ast
import collections.abc

tt = jack_scanner.TokenType


# How do I move this to conftest??
def _assert_next_lexeme(
    token_iter: collections.abc.Iterator[jack_scanner.Token],
    lexemes: collections.abc.Iterator[str],
):
    while cur := next(lexemes, None):
        assert next(token_iter).lexeme == cur


def assert_lexemes(
    token_iterable: collections.abc.Iterable, lexemes: collections.abc.Iterable[str]
):
    lexeme_iter = iter(lexemes)
    _assert_next_lexeme(iter(token_iterable), lexeme_iter)
    return lexeme_iter


def test_return_statement():
    scanner = jack_scanner.Scanner(src="return 99 + 1;")
    scanner.scan()

    token_iter = assert_lexemes(scanner.tokens, ["return", "99", "+", "1", ";"])
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    return_statement = parser.return_statement()

    assert return_statement.return_kw.lexeme == "return"
    assert isinstance(return_statement.expression, jack_ast.Expression)
    assert return_statement.semicolon.lexeme == ";"


def test_do_statement():
    scanner = jack_scanner.Scanner(src="do game.run();")
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "do"
    assert next(token_iter).lexeme == "game"
    assert next(token_iter).lexeme == "."
    assert next(token_iter).lexeme == "run"
    assert next(token_iter).lexeme == "("
    assert next(token_iter).lexeme == ")"
    assert next(token_iter).lexeme == ";"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    do_statement = parser.do_statement()

    assert do_statement.do_kw.lexeme == "do"
    assert isinstance(do_statement.subroutine_call, jack_ast.SubroutineCall)
    assert do_statement.semicolon.lexeme == ";"


def test_let_statement():
    scanner = jack_scanner.Scanner(src='let s = "string constant";')
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "let"
    assert next(token_iter).lexeme == "s"
    assert next(token_iter).lexeme == "="
    assert next(token_iter).lexeme == "string constant"
    assert next(token_iter).lexeme == ";"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    let_statement = parser.let_statement()

    assert let_statement.let_kw.lexeme == "let"
    assert let_statement.var_name.lexeme == "s"
    assert let_statement.equal.lexeme == "="
    assert let_statement.expression.term.term.token_type == tt.STRING_CONSTANT
    assert let_statement.semi_colon.token_type == tt.SEMICOLON


def test_let_statement_with_index():
    scanner = jack_scanner.Scanner(src='let s[10] = "string constant";')
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "let"
    assert next(token_iter).lexeme == "s"
    assert next(token_iter).lexeme == "["
    assert next(token_iter).lexeme == "10"
    assert next(token_iter).lexeme == "]"
    assert next(token_iter).lexeme == "="
    assert next(token_iter).lexeme == "string constant"
    assert next(token_iter).lexeme == ";"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    let_statement = parser.let_statement()

    assert let_statement.let_kw.lexeme == "let"
    assert let_statement.var_name.lexeme == "s"
    assert let_statement.equal.lexeme == "="
    assert let_statement.expression.term.term.token_type == tt.STRING_CONSTANT
    assert let_statement.semi_colon.token_type == tt.SEMICOLON
    assert let_statement.index_var[1].term.term.lexeme == "10"


def test_let_statement_from_parse_statement():
    scanner = jack_scanner.Scanner(src='let s[10] = "string constant";')
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "let"
    assert next(token_iter).lexeme == "s"
    assert next(token_iter).lexeme == "["
    assert next(token_iter).lexeme == "10"
    assert next(token_iter).lexeme == "]"
    assert next(token_iter).lexeme == "="
    assert next(token_iter).lexeme == "string constant"
    assert next(token_iter).lexeme == ";"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    statements = parser.parse_statements()

    assert isinstance(statements, list)
    assert len(statements) == 1
    let_statement = statements[0]
    assert isinstance(let_statement, jack_ast.LetStatement)
    assert let_statement.let_kw.lexeme == "let"
    assert let_statement.var_name.lexeme == "s"
    assert let_statement.equal.lexeme == "="
    assert let_statement.expression.term.term.token_type == tt.STRING_CONSTANT
    assert let_statement.semi_colon.token_type == tt.SEMICOLON
    assert let_statement.index_var[1].term.term.lexeme == "10"


def test_if_statement():
    scanner = jack_scanner.Scanner(
        src="""
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
        """
    )
    scanner.scan()

    parser = jack_parser.Parser(scanner.tokens)

    if_statement = parser.statement()

    assert isinstance(if_statement, jack_ast.IfStatement)
    assert if_statement.if_kw.lexeme == "if"
    assert if_statement.left_paren.lexeme == "("
    assert if_statement.expression.term.term.token_type == tt.FALSE
    assert if_statement.right_paren.lexeme == ")"
    assert if_statement.left_curly.lexeme == "{"

    assert len(if_statement.statements) == 3
    assert if_statement.optional_else[0].lexeme == "else"
    assert if_statement.optional_else[1].lexeme == "{"
    else_statements = if_statement.optional_else[2]
    assert len(else_statements) == 3
    assert if_statement.optional_else[3].lexeme == "}"


def test_while_statement():
    scanner = jack_scanner.Scanner(
        src="""
        while (~(key = 0)) {
            let key = Keyboard.keyPressed();
            do moveSquare();
        }
        """
    )
    scanner.scan()

    parser = jack_parser.Parser(scanner.tokens)

    while_statement = parser.statement()

    assert isinstance(while_statement, jack_ast.WhileStatement)
    assert while_statement.while_kw.lexeme == "while"
    assert while_statement.left_paren.lexeme == "("
    assert isinstance(while_statement.expression, jack_ast.Expression)
    assert while_statement.right_paren.lexeme == ")"
    assert while_statement.left_curly.lexeme == "{"

    assert len(while_statement.statements) == 2
    assert isinstance(while_statement.statements[0], jack_ast.LetStatement)
    assert isinstance(while_statement.statements[1], jack_ast.DoStatement)
    assert while_statement.right_curly.lexeme == "}"


def test_parse_statements():
    scanner = jack_scanner.Scanner(
        src="""

        while (~exit) {
            // waits for a key to be pressed
            while (key = 0) {
                let key = Keyboard.keyPressed();
                do moveSquare();
            }
            if (key = 81)  { let exit = true; }     // q key
            if (key = 90)  { do square.decSize(); } // z key
            if (key = 88)  { do square.incSize(); } // x key
            if (key = 131) { let direction = 1; }   // up arrow
            if (key = 133) { let direction = 2; }   // down arrow
            if (key = 130) { let direction = 3; }   // left arrow
            if (key = 132) { let direction = 4; }   // right arrow

            // waits for the key to be released
            while (~(key = 0)) {
                let key = Keyboard.keyPressed();
                do moveSquare();
            }
        }
        """
    )
    scanner.scan()

    parser = jack_parser.Parser(scanner.tokens)

    statements = parser.parse_statements()

    top_while_statement = statements[0]
    assert isinstance(top_while_statement, jack_ast.WhileStatement)
    while_statements = top_while_statement.statements
    assert len(while_statements) == 9
    assert isinstance(while_statements[5], jack_ast.IfStatement)
    # assert while_statement.while_kw.lexeme == "while"
    # assert while_statement.left_paren.lexeme == "("
    # assert isinstance(while_statement.expression, jack_ast.Expression)
    # assert while_statement.right_paren.lexeme == ")"
    # assert while_statement.left_curly.lexeme == "{"

    # assert len(while_statement.statements) == 2
    # assert isinstance(while_statement.statements[0], jack_ast.LetStatement)
    # assert isinstance(while_statement.statements[1], jack_ast.DoStatement)
    # assert while_statement.right_curly.lexeme == "}"
