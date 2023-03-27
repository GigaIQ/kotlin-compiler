from abc import ABC, abstractmethod
from typing import Callable, Tuple, Optional, Any, List
from enum import Enum


class AstNode(ABC):
    def __init__(self, row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__()
        self.row = row
        self.line = line
        for k, v in props.items():
            setattr(self, k, v)

    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return ()

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    def tree(self) -> [str, ...]:
        res = [str(self)]
        childs_temp = self.childs
        for i, child in enumerate(childs_temp):
            ch0, ch = '├', '│'
            if i == len(childs_temp) - 1:
                ch0, ch = '└', ' '
            res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        return res

    def visit(self, func: Callable[['AstNode'], None]) -> None:
        func(self)
        map(func, self.childs)

    def __getitem__(self, index):
        return self.childs[index] if index < len(self.childs) else None


class ExprNode(AstNode):
    pass


class LiteralNode(ExprNode):
    def __init__(self, literal: str,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.literal = literal

    def __str__(self) -> str:
        return self.literal


class IdentNode(ExprNode):
    def __init__(self, name: str,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)


class BinOp(Enum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'
    GE = '>='
    LE = '<='
    NEQUALS = '<>'
    EQUALS = '=='
    GT = '>'
    LT = '<'
    LOGICAL_AND = '&&'
    LOGICAL_OR = '||'


class Bools(Enum):
    TRUE = 'true'
    FALSE = 'false'


class BinOpNode(ExprNode):
    def __init__(self, op: BinOp, arg1: ExprNode, arg2: ExprNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def childs(self) -> Tuple[ExprNode, ExprNode]:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.op.value)


class StmtNode(ExprNode):
    pass


class TypeNode(IdentNode):
    def __init__(self, name: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(name, row=row, col=col, **props)
        self.type = None

    @property
    def childs(self):
        return []


class Decl(Enum):
    VAR = 'var'
    VAL = 'val'


class AssignNode(StmtNode):
    def __init__(self, var: Decl, val: ExprNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.var = var
        self.val = val

    @property
    def childs(self) -> Tuple[IdentNode, ExprNode]:
        return self.var, self.val

    def __str__(self) -> str:
        return '='


class VarNode(StmtNode):
    def __init__(self, declare: Decl, *params,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.declare = declare
        params = params[0:]
        sep = params[1]
        self.ident = params[0]
        self.type = None
        if isinstance(sep, str):
            self.type = params[2]
            self.var = params[3]
        else:
            self.var = params[1]

    def __str__(self) -> str:
        return str(self.declare)

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        childs = []
        if self.type is not None:
            childs.append(self.type)
        childs.append(self.ident)
        if self.var is not None:
            childs.append(self.var)
        return childs


class ParamNode(StmtNode):
    def __init__(self, name: IdentNode, type_: TypeNode, expr: ExprNode = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.type = type_
        self.name = name
        self.value = expr

    def __str__(self) -> str:
        return str(self.type)

    @property
    def childs(self):
        childs = [self.name]
        if self.value is not None:
            childs.append(self.value)
        return childs


class FuncDeclNode(StmtNode):
    def __init__(self, type_: IdentNode, name: IdentNode, params: ParamNode, body: StmtNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.type = type_
        self.name = name
        self.params = params
        self.body = body

    def __str__(self) -> str:
        return 'function'

    @property
    def childs(self) -> tuple[IdentNode, IdentNode, ParamNode, StmtNode]:
        return self.type, self.name, self.params, self.body


class CallNode(StmtNode):
    def __init__(self, func: IdentNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.func = func

    @property
    def childs(self) -> Tuple[IdentNode, ...]:
        return self.func,

    def __str__(self) -> str:
        return 'call'


class IfNode(StmtNode):
    def __init__(self, cond: ExprNode, then_stmt: StmtNode, else_stmt: Optional[StmtNode] = None):
        super().__init__()
        self.cond = cond
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return (self.cond, self.then_stmt) + ((self.else_stmt,) if self.else_stmt else tuple())

    def __str__(self):
        return 'if'


class StmtListNode(StmtNode):
    def __init__(self, *exprs: StmtNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.exprs = exprs

    @property
    def childs(self) -> Tuple[StmtNode, ...]:
        return self.exprs

    def __str__(self) -> str:
        return '...'


class WhileNode(StmtNode):
    def __init__(self, cond: ExprNode, body: StmtListNode,
                 row: Optional[int] = None, line: Optional[int] = None, **props):
        super().__init__(row=row, line=line, **props)
        self.cond = cond
        self.body = body

    @property
    def childs(self) -> Tuple[ExprNode, StmtListNode]:
        return self.cond, self.body

    def __str__(self) -> str:
        return 'while'


_empty = StmtListNode()
