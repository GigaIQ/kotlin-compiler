import os
import mel_parser


def main():
    prog = '''
        var a int
    '''
    prog = mel_parser.parse(prog)
    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()
