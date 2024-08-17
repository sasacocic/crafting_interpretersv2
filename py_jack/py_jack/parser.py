import py_jilox.scanner as scanner


class Parser:
    """
    recursive descent parser
    """

    tokens: list[scanner.Token]
