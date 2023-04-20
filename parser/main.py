import os
import mel_parser
import semantic


def execute(prog: str) -> None:
    prog = mel_parser.parse(prog)

    print('ast:')
    print(*prog.tree, sep=os.linesep)
    print()

    print('semantic_check:')
    try:
        scope = semantic.prepare_global_scope()
        prog.semantic_check(scope)
        print(*prog.tree, sep=os.linesep)
    except semantic.SemanticException as e:
        print('Ошибка: {}'.format(e.message))
        return
    print()


def main():
    prog = '''
        var a: Iasdnt = 2
        var b = 3
        val c: Float = 3.6
        b = 4
        while (a < 3) {
        a = 2 + 2
        b = 3
        }

        '''

    # prog = mel_parser.parse(prog)
    # print(*prog.tree, sep=os.linesep)
    execute(prog)


if __name__ == "__main__":
    main()
