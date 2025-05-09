"""Module defining dice expression and rolling behavior

Hakase possesses a rich dice expression rolling, and probability calculation system.
That system is defined entirely within this module. I'm gonna be brutally honest,
I scarcely understand what's going on in here, and I wrote the damn thing. But regardless...

The long and short of it is that Hakase conflates a dice result with an integer, and as such,
treats them the same. The evaluation of the expressions is done with a recursive compiler-like
principle that systematically evalutes the outcome, again, conflating dice outcomes with integers.

Computation of the 'probabilistic map' as it is called, is done with numpy and a bit of multinomial theorum,
which - again - I barely understand. (I'm sort of surprised any of this works tbh)
Modify this file at your own peril, lest you break everything.

    * WHITESPACE - String defining which characters are considered whitespace
    * DICE_CHARS - String defining which characters precede a dice
    * NUMBERS - String defining which characters are considered numbers

    * InterpreterException - General execption defining errors that occur within expression interpretation
    * dynamic_round - Helper function which rounds to a specific number of sigfigs
    * TokenType - Enum defining all possible tokens used by the interpreter
    * Token - Dataclass defining a token used by the interpreter
    * Die - Class defining a die and its outcome
    * DiceRoll - Class defining an entire set of dice rolls and the outcomes
    * NumNode - Class defining a number node used by the Parser. All subsequent nodes are similar in nature
    * Lexer - Class defining behavior for the expression lexer
    * Parser - Class defining behavior for the expression parser
    * Interpreter - Class defining behavior of the expression interpreter
"""


import copy
import dataclasses
import enum
import functools
import itertools
import math
import numpy
import random
import typing as t


WHITESPACE = " \n\t"
DICE_CHARS = "dD"
NUMBERS = "0123456789"


class InterpreterException(Exception):
    pass

def dynamic_round(number: float, sigfigs: int=3) -> float:
    return round(number, -int(math.floor(math.log10(abs(number)))) + (sigfigs - 1))


class TokenType(enum.Enum):
    NUM = 0
    DIE = 1
    ADD = 2
    SUB = 3
    MUL = 4
    DIV = 5
    POW = 6
    LPA = 7
    RPA = 8


@dataclasses.dataclass
class Token:
    type: TokenType
    value: any = None
    obj: any = None

    def __repr__(self):
        if self.obj is not None:
            if len(self.obj.dice) == 1:
                return f"{self.obj.number}d{self.obj.sides}: {self.value}"
            dice = " + ".join([str(die.outcome) for die in self.obj.dice])
            return f"{self.obj.number}d{self.obj.sides}: Σ({dice}) = {self.value}"
        return self.type.name + (f":{self.value}" if self.value is not None else "")


class Die(int):
    def __new__(cls, sides):
        outcome = random.randint(1, sides)
        self = super(Die, cls).__new__(cls, outcome)
        self.sides = sides
        self.outcome = outcome
        return self

    def __repr__(self):
        return f"<D{self.sides}: {self.outcome}>"

    @property
    def range(self):
        return range(1, self.sides+1)


class DiceRoll:
    def __init__(self, number: int, sides: int):
        self.number: int = number
        self.sides: int = sides

        self.dice = []
        for i in range(0, self.number):
            self.dice.append(Die(self.sides))

        self._outcome: t.Optional[int] = None

    @property
    def outcome(self) -> int:
        if self._outcome:
            return self._outcome
        return sum(self.dice)

    @property
    def range(self) -> range:
        return range(self.number, (self.sides*self.number)+1)

    @property
    def pmf(self) -> t.List[float]:
        p = numpy.ones(self.sides+1)
        p[0] = 0
        p /= self.sides
        return numpy.polynomial.polynomial.polypow(p, self.number)

    @staticmethod
    def probabilistic_map(self, *args) -> t.Dict[str, float]:
        sums = {}
        combinations = [list(die.range) for die in args]
        for combination in itertools.product(*combinations):
            try:
                sums[str(sum(combination))] += 1
            except KeyError:
                sums[str(sum(combination))] = 1

        all_possible = sum(sums.values())
        for s, value in sums.items():
            sums[s] = float(value) / all_possible
        return sums

    @property
    def probability(self) -> float:
        return self.probability_for(self.outcome)

    def probability_for(self, outcome: int) -> float:
        try:
            return self.pmf[outcome]
        except IndexError:
            return 0.0

    def set_outcome(self, number: int) -> None:
        self._outcome = number


@dataclasses.dataclass
class NumNode:
    value: any

    def __repr__(self) -> str:
        return f"{self.value}"


@dataclasses.dataclass
class AddNode:
    node_b: any
    node_a: any

    def __repr__(self) -> str:
        return f"({self.node_a}+{self.node_b})"


@dataclasses.dataclass
class SubNode:
    node_a: any
    node_b: any

    def __repr__(self) -> str:
        return f"({self.node_a}-{self.node_b})"


@dataclasses.dataclass
class MulNode:
    node_a: any
    node_b: any

    def __repr__(self) -> str:
        return f"({self.node_a}*{self.node_b})"


@dataclasses.dataclass
class DivNode:
    node_a: any
    node_b: any

    def __repr__(self) -> str:
        return f"({self.node_a}/{self.node_b})"


@dataclasses.dataclass
class PowNode:
    node_a: any
    node_b: any

    def __repr__(self) -> str:
        return f"({self.node_a}^{self.node_b})"


@dataclasses.dataclass
class PlusNode:
    node: any

    def __repr__(self) -> str:
        return f"(+{self.node})"


@dataclasses.dataclass
class MinusNode:
    node: any

    def __repr__(self) -> str:
        return f"(-{self.node})"


class Lexer:
    def __init__(self, text: str):
        self.text = iter(text)
        self.advance()

    def advance(self) -> None:
        try:
            self.current_char = next(self.text)
        except StopIteration:
            self.current_char = None

    def generate_tokens(self) -> t.Generator[Token, None, None]:
        while self.current_char is not None:
            if self.current_char in WHITESPACE:
                self.advance()
            elif self.current_char in (NUMBERS + DICE_CHARS):
                yield self.generate_number_or_dice()
            elif self.current_char == '+':
                self.advance()
                yield Token(TokenType.ADD)
            elif self.current_char == '-':
                self.advance()
                yield Token(TokenType.SUB)
            elif self.current_char == '*':
                self.advance()
                yield Token(TokenType.MUL)
            elif self.current_char == '/':
                self.advance()
                yield Token(TokenType.DIV)
            elif self.current_char == '(':
                self.advance()
                yield Token(TokenType.LPA)
            elif self.current_char == ')':
                self.advance()
                yield Token(TokenType.RPA)
            elif self.current_char == "^":
                self.advance()
                yield Token(TokenType.POW)
            else:
                raise InterpreterException(f"Illegal character '{self.current_char}'")

    def generate_number_or_dice(self) -> Token:
        num_left = self.current_char
        num_right = ""
        is_dice = False
        self.advance()

        while self.current_char is not None and self.current_char in (NUMBERS + DICE_CHARS):
            if num_left in DICE_CHARS:
                num_left = "1"
                num_right += self.current_char
                self.advance()
                is_dice = True
                continue
            if self.current_char in DICE_CHARS:
                self.advance()
                is_dice = True
                continue

            if is_dice is True:
                num_right += self.current_char
            else:
                num_left += self.current_char
            self.advance()

        if is_dice:
            roll = DiceRoll(int(num_left), int(num_right))
            return Token(TokenType.DIE, roll.outcome, roll)
        return Token(TokenType.NUM, int(num_left))


class Parser:
    def __init__(self, tokens: t.List[Token]):
        self.tokens = iter(tokens)
        self.advance()

    def advance(self) -> None:
        try:
            self.current_token = next(self.tokens)
        except StopIteration:
            self.current_token = None

    def parse(self):
        if self.current_token is None:
            return None

        result = self.expr()
        if self.current_token is not None:
            raise InterpreterException("A Syntax Error occurred.")

        return result

    def expr(self):
        result = self.term()

        while self.current_token is not None and self.current_token.type in (TokenType.ADD, TokenType.SUB):
            if self.current_token.type == TokenType.ADD:
                self.advance()
                result = AddNode(result, self.term())
            elif self.current_token.type == TokenType.SUB:
                self.advance()
                result = SubNode(result, self.term())

        return result

    def term(self):
        result = self.factor()

        while self.current_token is not None and self.current_token.type in (TokenType.POW, TokenType.MUL, TokenType.DIV):
            if self.current_token.type == TokenType.POW:
                self.advance()
                result = PowNode(result, self.factor())
            elif self.current_token.type == TokenType.MUL:
                self.advance()
                result = MulNode(result, self.factor())
            elif self.current_token.type == TokenType.DIV:
                self.advance()
                result = DivNode(result, self.factor())

        return result

    def factor(self):
        token = self.current_token

        if token.type == TokenType.LPA:
            self.advance()
            result = self.expr()

            if self.current_token.type is not TokenType.RPA:
                raise InterpreterException("A Syntax Error occurred: Missing right parenthesis.")

            self.advance()
            return result

        elif token.type in (TokenType.NUM, TokenType.DIE):
            self.advance()
            return(NumNode(token.value))

        elif token.type == TokenType.ADD:
            self.advance()
            return PlusNode(self.factor())

        elif token.type == TokenType.SUB:
            self.advance()
            return MinusNode(self.factor())

        raise InterpreterException("A Syntax Error occurred.")


class Interpreter:
    def __init__(self, text: str):
        self.text = text

        self.lexer = Lexer(self.text)
        self.tokens = list(self.lexer.generate_tokens())

        self.node = self.parse(self.tokens)

    @property
    def dice_tokens(self) -> t.List[Die]:
        return list(filter(lambda x: x.type == TokenType.DIE, self.tokens))

    def parse(self, tokens: t.List[Token]):
        return Parser(tokens).parse()

    def interpret(self, node=None):
        if node is None:
            node = self.node

        if type(node) is NumNode:
            return node.value
        elif type(node) is AddNode:
            return self.interpret(node.node_a) + self.interpret(node.node_b)
        elif type(node) is SubNode:
            return self.interpret(node.node_a) - self.interpret(node.node_b)
        elif type(node) is MulNode:
            return self.interpret(node.node_a) * self.interpret(node.node_b)
        elif type(node) is DivNode:
            return self.interpret(node.node_a) / self.interpret(node.node_b)
        elif type(node) is PowNode:
            return self.interpret(node.node_a) ** self.interpret(node.node_b)

    def get_interpreter_for_values(self, outcomes):
        if len(outcomes) != len(self.dice_tokens):
            raise ValueError(f"Expected {len(self.dice_tokens)} values, got {len(outcomes)}.")

        idx = 0
        new_tokens = []
        for i, token in enumerate(self.tokens):
            if token.type == TokenType.DIE:
                token.obj._outcome = outcomes[idx]
                token.value = outcomes[idx]
                idx += 1
            new_tokens.append(token)

        new_interp = copy.copy(self)
        new_interp.tokens = new_tokens
        new_interp.node = new_interp.parse(new_interp.tokens)
        return new_interp

    @property
    def compound_probability(self):
        total = 1
        for token in self.dice_tokens:
            total *= token.obj.probability
        return total

    def get_output_string(self):
        if self.dice_tokens:
            output = f"Rolling: `{self.text}`\n```"
            for die in self.dice_tokens:
                output += f"{die} ({dynamic_round(die.obj.probability * 100)}%)\n"
            output += "```\nOutcome:\n```"
            outcome = self.interpret()
            if str(self.node) == str(outcome):
                output += f"{outcome}```"
            else:
                output += f"\n{self.node} = {outcome} ({dynamic_round(self.compound_probability * 100)}%)```"
            return output
        else:
            return f"No dice tokens have been specified in the expression `{self.text}`, so the outcome is a constant:\n```{self.interpret()}```"

    @functools.lru_cache
    def compute_distribution(self):
        outcome_combos = []
        map = {}
        for token in self.dice_tokens:
            outcome_combos.append(list(token.obj.range))
        outcome_combos = list(itertools.product(*outcome_combos))
        for combo in outcome_combos:
            interp = self.get_interpreter_for_values(combo)
            outcome = interp.interpret()
            try:
                map[outcome] += interp.compound_probability
            except KeyError:
                map[outcome] = interp.compound_probability

        sorted_map = {}
        for key in sorted(map.keys()):
            sorted_map[key] = map[key]

        map = {}
        keys = list(sorted_map.keys())
        for i in range(keys[0], keys[-1]+1):
            try:
                map[i] = sorted_map[i]
            except KeyError:
                map[i] = 0.0
        return map
