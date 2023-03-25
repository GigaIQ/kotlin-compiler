import inspect
from contextlib import suppress

import pyparsing as pp
from pyparsing import pyparsing_common as ppc

from mel_ast import *


def make_parser():
    num = pp.Regex('[+-]?\\d+\\.?\\d*([eE][+-]?\\d+)?')
    str_ = pp.QuotedString('"', escChar='\\', unquoteResults=False, convertWhitespaceEscapes=False)
    literal = num | str_
    bool_val = pp.Literal("true") | pp.Literal("false")
    literal = num | bool_val
    ident = ppc.identifier.setName('ident')

    INT = pp.Keyword("Integer").suppress()
    CHAR = pp.Keyword("Char").suppress()
    BOOL = pp.Keyword("Boolean").suppress()

    VAR = pp.Keyword("var").suppress()
    VAL = pp.Keyword("val").suppress()

    type_spec = INT | BOOL | CHAR

    ADD = pp.Keyword("+").suppress()
    SUB = pp.Keyword("-").suppress()
    MUL = pp.Keyword("*").suppress()
    DIV = pp.Keyword("/").suppress()
    AND = pp.Keyword("&&").suppress()
    OR = pp.Keyword("||").suppress()
    GE = pp.Keyword(">=").suppress()
    LE = pp.Keyword("<=").suppress()
    NEQUALS = pp.Keyword("!=").suppress()
    EQUALS = pp.Keyword("==").suppress()
    GT = pp.Keyword(">").suppress()
    LT = pp.Keyword("<").suppress()

    LPAR, RPAR = pp.Literal('(').suppress(), pp.Literal(')').suppress()
    LBRACK, RBRACK = pp.Literal("[").suppress(), pp.Literal("]").suppress()
    LBRACE, RBRACE = pp.Literal("{").suppress(), pp.Literal("}").suppress()

    ASSIGN = pp.Literal('=')

    type_ = pp.Forward()
    stmt = pp.Forward()
    stmt_list = pp.Forward()
    expr = pp.Forward()

    group = (
        num |
        str_ |
        ident |
        LPAR + expr + RPAR
    )

    mult = group + pp.ZeroOrMore(MUL | DIV + group).setName("bin_op")
    add = mult + pp.ZeroOrMore(ADD | SUB + mult).setName("bin_op")

    compare1 = pp.Group(add + pp.Optional((GE | LE | GT | LT) + add)).setName('bin_op')
    compare2 = pp.Group(compare1 + pp.Optional((EQUALS | NEQUALS) + compare1)).setName('bin_op')
    logical_and = pp.Group(compare2 + pp.ZeroOrMore(AND + compare2)).setName('bin_op')
    logical_or = pp.Group(logical_and + pp.ZeroOrMore(OR + logical_and)).setName('bin_op')

    expr << logical_or

    stmt_group = LBRACE + stmt_list + RBRACE

    type_ << ident

    var_type = ident + pp.Keyword(":").suppress() + type_

    assing = ident + ASSIGN + expr

    var_decl = VAR + var_type + ASSIGN + expr

    simple_stmt = assing

    stmt << (
        var_decl
        | simple_stmt
    )

    stmt_list = pp.ZeroOrMore(stmt)

    program = stmt_list.ignore(pp.cStyleComment).ignore(pp.dblSlashComment) + pp.StringEnd()

    start = program


    def set_parse_action_magic(rule_name: str, parser: pp.ParserElement) -> None:
        if rule_name == rule_name.upper():
            return
        if getattr(parser, 'name', None) and parser.name.isidentifier():
            rule_name = parser.name
        if rule_name in ('bin_op',):
            def bin_op_parse_action(s, loc, tocs):
                node = tocs[0]
                if not isinstance(node, AstNode):
                    node = bin_op_parse_action(s, loc, node)
                for i in range(1, len(tocs) - 1, 2):
                    secondNode = tocs[i + 1]
                    if not isinstance(secondNode, AstNode):
                        secondNode = bin_op_parse_action(s, loc, secondNode)
                    node = BinOpNode(BinOp(tocs[i]), node, secondNode)
                return node

            parser.setParseAction(bin_op_parse_action)
        else:
            cls = ''.join(x.capitalize() for x in rule_name.split('_')) + 'Node'
            with suppress(NameError):
                cls = eval(cls)
                if not inspect.isabstract(cls):
                    def parse_action(s, loc, tocs):
                        return cls(*tocs)

                    parser.setParseAction(parse_action)

    for var_name, value in locals().copy().items():
        if isinstance(value, pp.ParserElement):
            set_parse_action_magic(var_name, value)

    return start


parser = make_parser()


def parse(prog: str) -> StmtListNode:
    return parser.parseString(str(prog))[0]


