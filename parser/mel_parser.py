import inspect
from _ast import BinOp
from contextlib import suppress

import pyparsing as pp
from pyparsing import pyparsing_common as ppc

from mel_ast import *


def _make_parser():
    IF = pp.Keyword('if')
    ELSE = pp.Keyword('else')
    WHILE = pp.Keyword('while')
    RETURN = pp.Keyword('return')
    FOR = pp.Keyword('for')
    IN = pp.Keyword('in')
    VAR = pp.Keyword('var')
    VAL = pp.Keyword('val')
    FUN = pp.Keyword('fun')
    keywords = IF | WHILE | RETURN | VAR | VAL | FUN
    SEMI, COMMA, COLON, DOTS = pp.Literal(';').suppress(), pp.Literal(',').suppress(), pp.Literal(':'), pp.Literal('..')

    num = pp.Regex('[+-]?\\d+\\.?\\d*([eE][+-]?\\d+)?')

    str_ = pp.QuotedString('"', escChar='\\', unquoteResults=False, convertWhitespaceEscapes=False)
    bool_ = pp.Regex('true|false')
    literal = num | str_ | bool_

    ident = (~keywords + ppc.identifier.copy()).setName('ident')
    type_ = pp.Forward()

    LPAR, RPAR = pp.Literal('(').suppress(), pp.Literal(')').suppress()
    LBRACK, RBRACK = pp.Literal("[").suppress(), pp.Literal("]").suppress()
    LBRACE, RBRACE = pp.Literal("{").suppress(), pp.Literal("}").suppress()
    type_ << ident
    ASSIGN = pp.Literal('=')

    ADD, SUB = pp.Literal('+'), pp.Literal('-')
    MUL, DIV, MOD = pp.Literal('*'), pp.Literal('/'), pp.Literal('%')
    AND = pp.Literal('&&')
    OR = pp.Literal('||')
    GE, LE, GT, LT = pp.Literal('>='), pp.Literal('<='), pp.Literal('>'), pp.Literal('<')
    NEQUALS, EQUALS = pp.Literal('!='), pp.Literal('==')

    add = pp.Forward()
    expr = pp.Forward()
    stmt = pp.Forward()
    stmt_list = pp.Forward()

    call = ident + LPAR + pp.Optional(expr + pp.ZeroOrMore(COMMA + expr)) + RPAR
    group = (
            literal |
            call |
            ident |
            LPAR + expr + RPAR
    )

    mult = pp.Group(group + pp.ZeroOrMore((MUL | DIV | MOD) + group)).setName('bin_op')
    add << pp.Group(mult + pp.ZeroOrMore((ADD | SUB) + mult)).setName('bin_op')
    seq = pp.Group(add + pp.Optional(DOTS + add + pp.Optional(expr))).setName('bin_op')
    compare1 = pp.Group(seq + pp.Optional((GE | LE | GT | LT) + seq)).setName('bin_op')
    compare2 = pp.Group(compare1 + pp.Optional((EQUALS | NEQUALS) + compare1)).setName('bin_op')
    logical_and = pp.Group(compare2 + pp.ZeroOrMore(AND + compare2)).setName('bin_op')
    logical_or = pp.Group(logical_and + pp.ZeroOrMore(OR + logical_and)).setName('bin_op')

    expr << logical_or

    simple_assign = (ident + ASSIGN.suppress() + expr).setName('assign')
    var_ = (VAR | VAL) + ((ident + COLON + type_ + pp.Optional(ASSIGN.suppress() + expr)) |
                          (ident + pp.Optional(ASSIGN.suppress() + expr)))

    assign = ident + ASSIGN.suppress() + expr
    simple_stmt = assign | call

    if_ = IF.suppress() + LPAR + expr + RPAR + stmt + pp.Optional(ELSE.suppress() + stmt)
    while_ = WHILE.suppress() + LPAR + expr + RPAR + stmt
    for_ = FOR.suppress() + LPAR + ident + IN.suppress() + expr + RPAR + stmt
    return_ = RETURN.suppress() + pp.Optional(expr)
    comp_op = LBRACE + stmt_list + RBRACE

    param = ident + COLON.suppress() + type_
    params = param + pp.ZeroOrMore(COMMA + param)
    func_decl = FUN.suppress() + ident + LPAR + pp.Optional(params) + RPAR + pp.Optional(
        COLON.suppress() + type_) + LBRACE + stmt_list + RBRACE

    stmt << (
            if_ |
            while_ |
            for_ |
            return_ |
            simple_stmt |
            var_ |
            comp_op |
            func_decl
    )

    stmt_list << (pp.ZeroOrMore(stmt))

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


parser = _make_parser()


def parse(prog: str) -> StmtListNode:
    return parser.parseString(str(prog))[0]
