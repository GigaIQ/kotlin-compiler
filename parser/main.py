import os
import mel_parser


def main():
    prog = '''
            a = 2
            b = 3
            if (a > 5) {
                b = 4
            } else {
                a = 4
            }
        '''
    prog = mel_parser.parse(prog)
    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()
