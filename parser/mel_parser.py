from contextlib import suppress

import pyparsing as pp
from pyparsing import pyparsing_common as ppc

from mel_ast import *


def _make_parser():
    # num = ppc.fnumber.setParseAction(lambda s, loc, tocs: tocs[0])
    num = pp.Regex('[+-]?\\d+\\.?\\d*([eE][+-]?\\d+)?')
    # c escape-последовательностями как-то неправильно работает
    str_ = pp.QuotedString('"', escChar='\\', unquoteResults=False, convertWhitespaceEscapes=False)
    literal = num | str_

    ident = ppc.identifier.setName('ident')

    identInt = ppc.identifier.setName('int')
    identChar = ppc.identifier.setName("char")
    identBool = ppc.identifier.setName("bool")

    idents = ident | identInt | identChar | identBool

    LPAR, RPAR = pp.Literal('(').suppress(), pp.Literal(')').suppress()
    LBRACK, RBRACK = pp.Literal("[").suppress(), pp.Literal("]").suppress()
    LBRACE, RBRACE = pp.Literal("{").suppress(), pp.Literal("}").suppress()
    SEMI, COMMA = pp.Literal(';').suppress(), pp.Literal(',').suppress()
    ASSIGN = pp.Literal('=')

    ADD, SUB = pp.Literal('+'), pp.Literal('-')
    MUL, DIV = pp.Literal('*'), pp.Literal('/')
    AND = pp.Literal('&&')
    OR = pp.Literal('||')
    BIT_AND = pp.Literal('&')
    BIT_OR = pp.Literal('|')
    GE, LE, GT, LT = pp.Literal('>='), pp.Literal('<='), pp.Literal('>'), pp.Literal('<')
    NEQUALS, EQUALS = pp.Literal('!='), pp.Literal('==')

    add = pp.Forward()
    expr = pp.Forward()
    stmt = pp.Forward()
    stmt_list = pp.Forward()

    group = ( ident | literal | LPAR + expr + RPAR )

    adv = pp.Keyword("var").suppress() + ident + idents

    mult = group + pp.ZeroOrMore(MUL + group).setName("bin_op")
    add << mult + pp.ZeroOrMore(ADD + mult)

    compare1 = pp.Group(add + pp.Optional((GE | LE | GT | LT) + add)).setName('bin_op')
    compare2 = pp.Group(compare1 + pp.Optional((EQUALS | NEQUALS) + compare1)).setName('bin_op')
    logical_and = pp.Group(compare2 + pp.ZeroOrMore(AND + compare2)).setName('bin_op')
    logical_or = pp.Group(logical_and + pp.ZeroOrMore(OR + logical_and)).setName('bin_op')

    expr << logical_or

    assign = ident + ASSIGN.suppress() + add

    if_ = pp.Keyword("if").suppress() + LPAR + expr + RPAR + stmt + pp.Optional(pp.Keyword("else")).suppress() + LBRACK + stmt_list + RBRACE

    for_condition = pp.Optional(assign + pp.Literal(";").suppress() & stmt + pp.Literal(";").suppress() & stmt)
    for_body = stmt_list

    for_ = pp.Keyword("for").suppress() + for_condition + LBRACE + for_body + RBRACE

    ident_list = ident + pp.ZeroOrMore(COMMA + ident)

    var_function_decl = ident + idents
    params = pp.ZeroOrMore(var_function_decl + pp.ZeroOrMore(COMMA + var_function_decl))
    function_call = pp.Keyword("fun").suppress() + ident + LPAR + params + RPAR

    stmt << ( assign | adv | if_| for_ | function_call )

    stmt_list = pp.ZeroOrMore(stmt)

    program = stmt_list.ignore(pp.cStyleComment).ignore(pp.dblSlashComment) + pp.StringEnd()

    start = program

    def set_parse_action_magic(rule_name: str, parser: pp.ParserElement) -> None:
        if rule_name == rule_name.upper():
            return
        if getattr(parser, 'name', None) and parser.name.isidentifier():
            rule_name = parser.name
        if rule_name in ('bin_op', ):
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
