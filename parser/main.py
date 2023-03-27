import os
import mel_parser


def main():
    prog = '''
        var a: Int = 2
        var b = 3
        val c: Float = 3
        b = 3
        while (a < 2) {
        a = 2
        b = 3
        }
        
        if (a % b == 2) {
            var c: Integer = 100
            sample()
        } else {
            sample()
        }
        
        fun sample(input1: Int) : Int {
            var var1 = 2
            var var2 = 2
            return var1
        }
        '''
    prog = mel_parser.parse(prog)
    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()
