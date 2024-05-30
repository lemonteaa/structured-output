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

class JSONToken(Enum):
    NULL = 1
    BOOL_T = 2
    BOOL_F = 3
    NUM = 4
    STR = 5
    LEFT_SQUARE_BRACKET = 6
    RIGHT_SQUARE_BRACKET = 7
    LEFT_CURLY_BRACKET = 8
    RIGHT_CURLY_BRACKET = 9
    COMMA = 10
    COLON = 11

class StackAction(Enum):
    NOOPS = 1
    PUSH = 2
    POP = 3

@dataclass
class CFG:
    state_transition : any
    pop_action : any
    token_class: Enum

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

simple_nested_list_grammar = CFG(simple_nested_list_cfg, simple_nested_list_pop_action, SimpleNestedList)

json_cfg = [
    {
        JSONToken.NULL: (-1, StackAction.NOOPS, 0, lambda d, t: (None, None)),
        JSONToken.BOOL_T: (-1, StackAction.NOOPS, 0, lambda d, t: (True, None)),
        JSONToken.BOOL_F: (-1, StackAction.NOOPS, 0, lambda d, t: (False, None)),
        JSONToken.NUM: (-1, StackAction.NOOPS, 0, lambda d, t: (float(t.value), None)),
        JSONToken.STR: (-1, StackAction.NOOPS, 0, lambda d, t: (t.value, None)),
        JSONToken.LEFT_SQUARE_BRACKET: (1, StackAction.NOOPS, 0, lambda d, t: (list(), None)),
        JSONToken.LEFT_CURLY_BRACKET: (3, StackAction.NOOPS, 0, lambda d, t: (dict(), None)),
    },
    {
        JSONToken.RIGHT_SQUARE_BRACKET: (-1, StackAction.NOOPS, 0, None),
        JSONToken.NULL: (2, StackAction.NOOPS, 0, lambda d, t: (d + [None], None)),
        JSONToken.BOOL_T: (2, StackAction.NOOPS, 0, lambda d, t: (d + [True], None)),
        JSONToken.BOOL_F: (2, StackAction.NOOPS, 0, lambda d, t: (d + [False], None)),
        JSONToken.NUM: (2, StackAction.NOOPS, 0, lambda d, t: (d + [float(t.value)], None)),
        JSONToken.STR: (2, StackAction.NOOPS, 0, lambda d, t: (d + [t.value], None)),
        JSONToken.LEFT_SQUARE_BRACKET: (1, StackAction.PUSH, 2, lambda d, t: (list(), d)),
        JSONToken.LEFT_CURLY_BRACKET: (3, StackAction.PUSH, 2, lambda d, t: (dict(), d))
    },
    {
        JSONToken.RIGHT_SQUARE_BRACKET: (-1, StackAction.NOOPS, 0, None),
        JSONToken.COMMA: (1, StackAction.NOOPS, 0, None)
    },
    {
        JSONToken.RIGHT_CURLY_BRACKET: (-1, StackAction.NOOPS, 0, None),
        JSONToken.STR: (6, StackAction.NOOPS, 0, lambda d, t: ((d, t.value), None))
    },
    {
        JSONToken.NULL: (5, StackAction.NOOPS, 0, lambda d, t: (dict(d[0], **{ d[1]: None}), None)),
        JSONToken.BOOL_T: (5, StackAction.NOOPS, 0, lambda d, t: (dict(d[0], **{ d[1]: True}), None)),
        JSONToken.BOOL_F: (5, StackAction.NOOPS, 0, lambda d, t: (dict(d[0], **{ d[1]: False}), None)),
        JSONToken.NUM: (5, StackAction.NOOPS, 0, lambda d, t: (dict(d[0], **{ d[1]: float(t.value) }), None)),
        JSONToken.STR: (5, StackAction.NOOPS, 0, lambda d, t: (dict(d[0], **{ d[1]: t.value }), None)),
        JSONToken.LEFT_SQUARE_BRACKET: (1, StackAction.PUSH, 5, lambda d, t: (list(), d)),
        JSONToken.LEFT_CURLY_BRACKET: (3, StackAction.PUSH, 5, lambda d, t: (dict(), d))
    },
    {
        JSONToken.RIGHT_CURLY_BRACKET: (-1, StackAction.NOOPS, 0, None),
        JSONToken.COMMA: (3, StackAction.NOOPS, 0, None)
    },
    {
        JSONToken.COLON: (4, StackAction.NOOPS, 0, None)
    }
]

def json_pop_action(cur_data, return_state, stack_data):
    if return_state == 2:
        return stack_data + [cur_data]
    elif return_state == 5:
        return dict(stack_data[0], **{ stack_data[1]: cur_data })
    else:
        raise ValueError(f"Unknown return: {return_state}")

json_grammar = CFG(json_cfg, json_pop_action, JSONToken)

class PDA:
    def __init__(self):
        self.stack = []
        self.state = 0
        self.data = None
    def __str__(self):
        return f"Stack: {self.stack}\nState: {self.state}\nData: {self.data}\n"
    def get_valid_next_token(self, cfg : CFG):
        return list(cfg.state_transition[self.state].keys())
    def run_step(self, cfg : CFG, token : GrammarToken) -> bool:
        m = cfg.state_transition[self.state]
        if cfg.token_class(token.type) not in m:
            raise ValueError(f"Invalid token: {token}")
        (next_state, stack_action, return_state, visitor) = m[cfg.token_class(token.type)]
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
            self.data = cfg.pop_action(self.data, return_state, stack_data)
            self.state = return_state
            return False
        else:
            return False
    def run_all(self, cfg : CFG, tokens, debug = False):
        finished = False
        for t in tokens:
            finished = self.run_step(cfg, t)
            if debug:
                print(f"Token: {t}")
                print(self)
                print("----")
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

test_json_1 = [
    GrammarToken(JSONToken.LEFT_CURLY_BRACKET.value, None),
    GrammarToken(JSONToken.STR.value, "id"),
    GrammarToken(JSONToken.COLON.value, None),
    GrammarToken(JSONToken.NUM.value, "4125"),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.STR.value, "book_title"),
    GrammarToken(JSONToken.COLON.value, None),
    GrammarToken(JSONToken.STR.value, "Introduction to Astronomy - Edition II"),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.STR.value, "reviews"),
    GrammarToken(JSONToken.COLON.value, None),
    GrammarToken(JSONToken.LEFT_SQUARE_BRACKET.value, None),
    GrammarToken(JSONToken.LEFT_CURLY_BRACKET.value, None),
    GrammarToken(JSONToken.RIGHT_CURLY_BRACKET.value, None),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.LEFT_CURLY_BRACKET.value, None),
    GrammarToken(JSONToken.STR.value, "reviewer"),
    GrammarToken(JSONToken.COLON.value, None),
    GrammarToken(JSONToken.STR.value, "John Doe"),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.STR.value, "rating"),
    GrammarToken(JSONToken.COLON.value, None),
    GrammarToken(JSONToken.NUM.value, "4.5"),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.RIGHT_CURLY_BRACKET.value, None),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.LEFT_CURLY_BRACKET.value, None),
    GrammarToken(JSONToken.STR.value, "reviewer"),
    GrammarToken(JSONToken.COLON.value, None),
    GrammarToken(JSONToken.STR.value, "Mary Ankinson"),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.STR.value, "rating"),
    GrammarToken(JSONToken.COLON.value, None),
    GrammarToken(JSONToken.NUM.value, "3.0"),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.RIGHT_CURLY_BRACKET.value, None),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.LEFT_CURLY_BRACKET.value, None),
    GrammarToken(JSONToken.STR.value, "reviewer"),
    GrammarToken(JSONToken.COLON.value, None),
    GrammarToken(JSONToken.STR.value, "annoymous"),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.STR.value, "rating"),
    GrammarToken(JSONToken.COLON.value, None),
    GrammarToken(JSONToken.NUM.value, "3.5"),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.RIGHT_CURLY_BRACKET.value, None),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.RIGHT_SQUARE_BRACKET.value, None),
    GrammarToken(JSONToken.COMMA.value, None),
    GrammarToken(JSONToken.STR.value, "is_ebook"),
    GrammarToken(JSONToken.COLON.value, None),
    GrammarToken(JSONToken.BOOL_T.value, None),
    GrammarToken(JSONToken.RIGHT_CURLY_BRACKET.value, None)
]

if __name__ == "__main__":
    pda = PDA()
    print(pda.run_all(simple_nested_list_grammar, test1))
    pda = PDA()
    print(pda.run_all(simple_nested_list_grammar, test2a, debug=False))
    pda = PDA()
    print(pda.run_all(json_grammar, test_json_1, debug=True))
