import py_jack.jack_scanner as jack_scanner
import py_jack.jack_parser as jack_parser
import typing
import os
import logging.config

# had to paste this in here, because the logging setup for tests is different than for __main__ - need to see if I can't do this for every single test
# in my pytest suite
LOG_LEVEL: typing.Final[str | None] = os.environ.get("LOG_LEVEL")

logging.config.dictConfig({
    "version": 1,
    "formatters": {
        "default": {"format": "[%(levelname)s][%(funcName)s:%(lineno)d] %(message)s"}
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    # TODO: notes py_jack.scanner and py_jack.parser do not exist I changed the names
    "loggers": {
        "py_jack.jack_scanner": {"level": LOG_LEVEL or logging.ERROR},
        "py_jack.jack_parser": {"level": LOG_LEVEL or logging.INFO},
        "py_jack.ast_nodes": {"level": LOG_LEVEL or logging.INFO},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL or logging.INFO},
})

token_type = jack_scanner.TokenType


def test_parse_whole_program():
    main_progarm = """

class Main {
    function void main() {
        var int some;
        let some = 1+1;
        return;
   }

}
    """

    scanner = jack_scanner.Scanner(src=main_progarm)

    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "class"
    assert next(token_iter).lexeme == "Main"
    assert next(token_iter).lexeme == "{"
    assert next(token_iter).lexeme == "function"
    assert next(token_iter).lexeme == "void"
    assert next(token_iter).lexeme == "main"
    assert next(token_iter).lexeme == "("
    assert next(token_iter).lexeme == ")"
    assert next(token_iter).lexeme == "{"
    assert next(token_iter).lexeme == "var"
    assert next(token_iter).lexeme == "int"
    assert next(token_iter).lexeme == "some"
    assert next(token_iter).lexeme == ";"
    assert next(token_iter).lexeme == "let"
    assert next(token_iter).lexeme == "some"
    assert next(token_iter).lexeme == "="
    assert next(token_iter).lexeme == "1"
    assert next(token_iter).lexeme == "+"
    assert next(token_iter).lexeme == "1"
    assert next(token_iter).lexeme == ";"
    assert next(token_iter).lexeme == "return"
    assert next(token_iter).lexeme == ";"
    assert next(token_iter).lexeme == "}"
    assert next(token_iter).lexeme == "}"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    prog = parser.parse()

    assert prog.subroutine_dec is not None
    assert len(prog.subroutine_dec) == 1
    assert len(prog.subroutine_dec[0].subroutine_body.var_decs) == 1
    assert prog.subroutine_dec[0].subroutine_body.var_decs[0].var_kw.lexeme == "var"
    assert prog.subroutine_dec[0].subroutine_body.var_decs[0]._type.lexeme == "int"
    assert prog.subroutine_dec[0].subroutine_body.var_decs[0].semi_colon.lexeme == ";"
    assert len(prog.subroutine_dec[0].subroutine_body.statements.statements) == 2
