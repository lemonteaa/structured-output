from dataclasses import dataclass
from enum import Enum

print("Hello")

@dataclass
class GrammarToken:
    type: int
    value: str

class SimpleNestedList(Enum):
    ATOM = 1
    LEFT_BRACKET = 2
    RIGHT_BRACKET = 3
    COMMA = 4

class StackAction(Enum):
    NOOPS = 1
    PUSH = 2
    POP = 3

# Push: lambda cur_data, token: (new_cur_data, stack_data)
# (next_state, stack_action, return_state, visitor)
simple_nested_list_cfg = [
    {
        SimpleNestedList.ATOM: (-1, StackAction.NOOPS, 0, lambda d, t: (t.value, None)),
        SimpleNestedList.LEFT_BRACKET: (1, StackAction.NOOPS, 0, lambda d, t: (list(), None))
    },
    {
        SimpleNestedList.RIGHT_BRACKET: (-1, StackAction.NOOPS, 0, None),
        SimpleNestedList.ATOM: (2, StackAction.NOOPS, 0, lambda d, t: (d + [t.value], None)),
        SimpleNestedList.LEFT_BRACKET: (1, StackAction.PUSH, 2, lambda d, t: (list(), d))
    },
    {
        SimpleNestedList.RIGHT_BRACKET: (-1, StackAction.NOOPS, 0, None),
        SimpleNestedList.COMMA: (1, StackAction.NOOPS, 0, None)
    }
]

def simple_nested_list_pop_action(cur_data, return_state, stack_data):
    return stack_data + [cur_data]

class PDA:
    def __init__(self):
        self.stack = []
        self.state = 0
        self.data = None
    def __str__(self):
        return f"Stack: {self.stack}\nState: {self.state}\nData: {self.data}\n"
    def run_step(self, cfg, token : GrammarToken) -> bool:
        m = cfg[self.state]
        if SimpleNestedList(token.type) not in m:
            raise ValueError(f"Invalid token: {token}")
        (next_state, stack_action, return_state, visitor) = m[SimpleNestedList(token.type)]
        if visitor is not None:
            (new_cur_data, stack_data) = visitor(self.data, token)
            if stack_action == StackAction.PUSH:
                self.stack.append((return_state, stack_data))
            self.data = new_cur_data
        self.state = next_state

        # End state pop stack
        if self.state == -1:
            if len(self.stack) == 0:
                return True
            (return_state, stack_data) = self.stack.pop()
            self.data = simple_nested_list_pop_action(self.data, return_state, stack_data)
            self.state = return_state
            return False
        else:
            return False
    def run_all(self, cfg, tokens, debug = False):
        finished = False
        for t in tokens:
            finished = self.run_step(cfg, t)
            if debug:
                print(self)
            if finished:
                break
        if not finished:
            raise ValueError("Incomplete parse")
        return self.data

test1 = [
    GrammarToken(SimpleNestedList.LEFT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.ATOM.value, "hi"),
    GrammarToken(SimpleNestedList.COMMA.value, None),
    GrammarToken(SimpleNestedList.ATOM.value, "bye"),
    GrammarToken(SimpleNestedList.COMMA.value, None),
    GrammarToken(SimpleNestedList.RIGHT_BRACKET.value, None)
]

test2 = [
    GrammarToken(SimpleNestedList.LEFT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.ATOM.value, "foo"),
    GrammarToken(SimpleNestedList.COMMA.value, None),
    GrammarToken(SimpleNestedList.LEFT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.ATOM.value, "sub1"),
    GrammarToken(SimpleNestedList.COMMA.value, None),
    GrammarToken(SimpleNestedList.ATOM.value, "sub2"),
    GrammarToken(SimpleNestedList.RIGHT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.COMMA.value, None),
    GrammarToken(SimpleNestedList.ATOM.value, "bar"),
    GrammarToken(SimpleNestedList.COMMA.value, None),
    GrammarToken(SimpleNestedList.LEFT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.RIGHT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.RIGHT_BRACKET.value, None),
]

test2a = [
    GrammarToken(SimpleNestedList.LEFT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.ATOM.value, "foo"),
    GrammarToken(SimpleNestedList.COMMA.value, None),
    GrammarToken(SimpleNestedList.LEFT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.LEFT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.ATOM.value, "sub11"),
    GrammarToken(SimpleNestedList.RIGHT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.COMMA.value, None),
    GrammarToken(SimpleNestedList.ATOM.value, "sub2"),
    GrammarToken(SimpleNestedList.RIGHT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.COMMA.value, None),
    GrammarToken(SimpleNestedList.ATOM.value, "bar"),
    GrammarToken(SimpleNestedList.COMMA.value, None),
    GrammarToken(SimpleNestedList.LEFT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.RIGHT_BRACKET.value, None),
    GrammarToken(SimpleNestedList.RIGHT_BRACKET.value, None),
]

if __name__ == "__main__":
    pda = PDA()
    print(pda.run_all(simple_nested_list_cfg, test1))
    pda = PDA()
    print(pda.run_all(simple_nested_list_cfg, test2a, debug=True))
