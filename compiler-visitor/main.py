from . import program


def main() -> None:
    prog1 = '''
        fun sample1() {
            println("Hello!")
        }
        fun pow(num: Int, p: Int) : Int {
            var t = num
            for(num in p) {
                num = num * t           
            }
            return num
        }
        fun main() {
            sample1()
            val res = pow(1, 2)
        }
    '''
    prog2 = '''
        var a : Int = 10
        var a : String = "A"
    '''
    prog3 = '''
        fun sample() : Double {
            return "AA"
        }
    '''
    prog4 = '''
            a = 4
        '''
    prog5 = '''
        val a: Int = 3
        var b = 3
        var c = 3
        for(a in 3) {
            var v = 3.2
        }

        fun sample(a: Int, b: Float) : Float {
            var g = 3
            return 43
        }

        var funRet = sample(b, c)
    '''
    program.execute(prog1)


if __name__ == "__main__":
    main()
