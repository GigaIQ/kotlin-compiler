import os
import mel_parser


def main():
    prog = '''
        var a: Int = 2
        var b = 3
        while (a < 2) {
        a = 2
        b = 3
        }
        
        a()
        
        fun a() {
        a = 2
        b = 3
        return b
        }
        '''
    prog = mel_parser.parse(prog)
    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()
