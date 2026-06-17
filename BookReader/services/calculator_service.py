class CalculatorService:

    @staticmethod
    def calculate(v1, v2, op):

        if op == "+":
            return v1 + v2

        if op == "-":
            return v1 - v2

        if op == "*":
            return v1 * v2

        if op == "/":

            if v2 == 0:
                raise ZeroDivisionError

            return v1 / v2

        raise ValueError