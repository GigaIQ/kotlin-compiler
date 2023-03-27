import os
import mel_parser


def main():
    prog = '''
        var a : int = 10
        var b : int
        val c = 10
        if(a == 10) { 
            println("a равно 10"); 
        }
    '''

    prog = mel_parser.parse(prog)
    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()
