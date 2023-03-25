from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Optional, Union, Tuple, Callable

class AstNode(ABC):
    """Базовый абстрактый класс узла AST-дерева
    """

    init_action: Callable[['AstNode'], None] = None

    def __init__(self, row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__()
        self.row = row
        self.col = col
        for k, v in props.items():
            setattr(self, k, v)
        if AstNode.init_action is not None:
            AstNode.init_action(self)

        self.node_ident = None

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return ()

    def to_str(self):
        return str(self)

    @property
    def tree(self) -> [str, ...]:
        r = [str(self)]
        childs = self.childs
        for i, child in enumerate(childs):
            ch0, ch = '├', '│'
            if i == len(childs) - 1:
                ch0, ch = '└', ' '
            r.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        return tuple(r)

    def __getitem__(self, index):
        return self.childs[index] if index < len(self.childs) else None


class _GroupNode(AstNode):
    """Класс для группировки других узлов (вспомогательный, в синтаксисе нет соотвествия)
    """

    def __init__(self, name: str, *childs: AstNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.name = name
        self._childs = childs

    def __str__(self) -> str:
        return self.name

    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return self._childs


class ExprNode(AstNode, ABC):
    """Абстракный класс для выражений в AST-дереве
    """

    pass


class LiteralNode(ExprNode):
    """Класс для представления в AST-дереве литералов (числа, строки, логическое значение)
    """

    def __init__(self, literal: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.literal = literal
        if literal in ('true', 'false'):
            self.value = bool(literal)
        else:
            self.value = eval(literal)

    def __str__(self) -> str:
        return self.literal


class IdentNode(ExprNode):
    """Класс для представления в AST-дереве идентификаторов
    """

    def __init__(self, name: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)


class TypeNode(IdentNode):
    """Класс для представления в AST-дереве типов данный
       (при появлении составных типов данных должен быть расширен)
    """

    def __init__(self, name: str, generic=None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(name, row=row, col=col, **props)
        self.generic = generic
        self.type = None

    def to_str_full(self):
        return self.to_str()

    @property
    def childs(self):
        return (self.generic, ) if self.generic else []


class SinOpNode(ExprNode):
    """Класс для представления в AST-дереве бинарных операций
    """

    def __init__(self,  arg: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.arg = arg

    def __str__(self) -> str:
        return str(self.op.value)

    @property
    def childs(self) -> Tuple[ExprNode]:
        return self.arg,


class SeqNode(ExprNode):
    """Класс для представления в AST-дереве бинарных операций
    """

    def __init__(self, startArg: ExprNode, seqOp: str, endArg: ExprNode,
                 stepArg: ExprNode = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.startArg = startArg
        self.seqOp = seqOp
        self.endArg = endArg
        self.stepArg = stepArg

    def __str__(self) -> str:
        return 'seq'

    @property
    def childs(self) -> Tuple[ExprNode, ExprNode]:
        return [self.startArg, self.seqOp, self.endArg] + [self.stepArg] if self.stepArg is not None else []



class CallNode(ExprNode):
    """Класс для представления в AST-дереве вызова функций
       (в языке программирования может быть как expression, так и statement)
    """

    def __init__(self, func: IdentNode, *params: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.func = func
        self.params = params

    def __str__(self) -> str:
        return 'call'

    @property
    def childs(self) -> Tuple[IdentNode, ...]:
        return (self.func, *self.params)


class BinOp(ExprNode):
    """Класс для представления в AST-дереве операций конвертации типов данных
       (в языке программирования может быть как expression, так и statement)
    """

    def __init__(self, expr: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.expr = expr

    def __str__(self) -> str:
        return 'convert'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return (_GroupNode(str(self.type), self.expr), )


# def type_convert(expr: ExprNode, type_: TypeDesc, except_node: Optional[AstNode] = None, comment: Optional[str] = None) -> ExprNode:
#     """Метод преобразования ExprNode узла AST-дерева к другому типу
#     :param expr: узел AST-дерева
#     :param type_: требуемый тип
#     :param except_node: узел, о которого будет исключение
#     :param comment: комментарий
#     :return: узел AST-дерева c операцией преобразования
#     """
#
#     if expr.node_type is None:
#         except_node.semantic_error('Тип выражения не определен')
#     if type_ is None:
#         except_node.node_type = expr.node_type
#         except_node.type = TypeNode(except_node.node_type.base_type)
#         return expr
#     if expr.node_type == type_:
#         return expr
#     if expr.node_type.is_simple and type_.is_simple and \
#             expr.node_type.base_type in TYPE_CONVERTIBILITY and type_.base_type in TYPE_CONVERTIBILITY[expr.node_type.base_type]:
#         return BinOp(expr, type_)
#     else:
#         (except_node if except_node else expr).semantic_error('Тип {0}{2} не конвертируется в {1}'.format(
#             expr.node_type, type_, ' ({})'.format(comment) if comment else ''
#         ))


class StmtNode(ExprNode, ABC):
    """Абстракный класс для деклараций или инструкций в AST-дереве
    """

    def to_str_full(self):
        return self.to_str()


class AssignNode(ExprNode):
    """Класс для представления в AST-дереве оператора присваивания
    """

    def __init__(self, var: IdentNode, val: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.var = var
        self.val = val

    def __str__(self) -> str:
        return '='

    @property
    def childs(self) -> Tuple[IdentNode, ExprNode]:
        return self.var, self.val


class VarsNode(StmtNode):
    """Класс для представления в AST-дереве объявления переменнных
    """

    def __init__(self, type_: TypeNode, *vars_: Union[IdentNode, 'AssignNode'],
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.type = type_
        self.vars = vars_

    def __str__(self) -> str:
        return str(self.type)

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self.vars


class VarNode(StmtNode):
    """Класс для представления в AST-дереве объявления переменнных
    """

    def __init__(self, *params,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.declare = params[0]
        params = params[1:]
        sep = params[1]
        self.ident = params[0]
        self.type = None
        self.var = None
        if isinstance(sep, str):
            self.type = params[2]
            if len(params) > 3:
                self.var = params[3]
        else:
            self.var = params[1]

    def __str__(self) -> str:
        return self.declare

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        childs = []
        if self.type is not None:
            childs.append(self.type)
        childs.append(self.ident)
        if self.var is not None:
            childs.append(self.var)
        return childs


class BinOpNode(ExprNode):
    """Класс для представления в AST-дереве бинарных операций
    """

    def __init__(self, op: BinOp, arg1: ExprNode, arg2: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    def __str__(self) -> str:
        return str(self.op)

    @property
    def childs(self) -> Tuple[ExprNode, ExprNode]:
        return self.arg1, self.arg2


class ReturnNode(StmtNode):
    """Класс для представления в AST-дереве оператора return
    """

    def __init__(self, val: ExprNode = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.val = val

    def __str__(self) -> str:
        return 'return'

    @property
    def childs(self) -> Tuple[ExprNode]:
        return (self.val, ) if self.val is not None else ()


class IfNode(StmtNode):
    """Класс для представления в AST-дереве условного оператора
    """

    def __init__(self, cond: ExprNode, then_stmt: StmtNode, else_stmt: Optional[StmtNode] = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.cond = cond
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

    def __str__(self) -> str:
        return 'if'

    @property
    def childs(self) -> Tuple[ExprNode, StmtNode, Optional[StmtNode]]:
        return (self.cond, self.then_stmt, *((self.else_stmt,) if self.else_stmt else tuple()))

class ForNode(StmtNode):
    """Класс для представления в AST-дереве цикла for
    """

    def __init__(self, init: IdentNode, seq: ExprNode, body: StmtNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.init = init
        self.seq = seq
        self.body = body

    def __str__(self) -> str:
        return 'for'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self.init, self.seq, self.body


class WhileNode(StmtNode):
    """Класс для представления в AST-дереве цикла while
    """

    def __init__(self, condition: ExprNode, body: StmtNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.condition = condition
        self.body = body

    def __str__(self) -> str:
        return 'while'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self.condition, self.body

class DoWhileNode(StmtNode):
    """Класс для представления в AST-дереве цикла while
    """

    def __init__(self, body: StmtNode, condition: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.condition = condition
        self.body = body

    def __str__(self) -> str:
        return 'do while'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self.condition, self.body


class ParamNode(StmtNode):
    """Класс для представления в AST-дереве объявления параметра функции
    """

    def __init__(self, name: IdentNode, type_: TypeNode, expr: ExprNode = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.type = type_
        self.name = name
        self.value = expr

    def __str__(self) -> str:
        return str(self.type)

    @property
    def childs(self) -> Tuple[IdentNode]:
        childs = [self.name]
        if self.value is not None:
            childs.append(self.value)
        return childs

class FuncNode(StmtNode):
    """Класс для представления в AST-дереве объявления функции
    """

    def __init__(self, type_: TypeNode, name: IdentNode, params: Tuple[ParamNode], body: StmtNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.type = type_ if type_ is not None else TypeNode('Void')
        self.name = name
        self.params = params
        self.body = body

    def __str__(self) -> str:
        return 'function'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return _GroupNode(str(self.type), self.name), _GroupNode('params', *self.params), self.body


class StmtListNode(StmtNode):
    """Класс для представления в AST-дереве последовательности инструкций
    """

    def __init__(self, *exprs: StmtNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.exprs = exprs
        self.program = False

    def __str__(self) -> str:
        return '...'

    @property
    def childs(self) -> Tuple[StmtNode, ...]:
        return self.exprs


EMPTY_STMT = StmtListNode()
