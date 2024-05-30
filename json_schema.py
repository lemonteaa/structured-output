from basic_parse import *

import random

from util import *

print("Random select")

def gen_json_token(token_type : JSONToken) -> GrammarToken:
    val = None
    if token_type == JSONToken.NUM:
        val = str(random.uniform(-100.0, +100.0))
    if token_type == JSONToken.STR:
        val = random_name()
    return GrammarToken(token_type.value, val)

def complete_partial_json(cur_data, parse_stack):
    for (return_state, stack_data) in reversed(parse_stack):
        cur_data = json_grammar.pop_action(cur_data, return_state, stack_data)
    return cur_data

def random_json(max_tokens : int):
    pda = PDA()
    finished = False
    init = True
    for i in range(max_tokens):
        if init:
            possible_next_token = [JSONToken.LEFT_CURLY_BRACKET, JSONToken.LEFT_SQUARE_BRACKET]
            init = False
        else:
            possible_next_token = list(json_grammar.state_transition[pda.state].keys())
        random_token = gen_json_token(random.choice(possible_next_token))
        finished = pda.run_step(json_grammar, random_token)
        if finished:
            break
    if not finished:
        return complete_partial_json(pda.data, pda.stack)
    else:
        return pda.data

if __name__ == "__main__":
    for i in range(5):
        print(random_json(random.randint(20, 120)))
