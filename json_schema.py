from basic_parse import *

import random
from enum import Enum

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
            possible_next_token = pda.get_valid_next_token(json_grammar)
        random_token = gen_json_token(random.choice(possible_next_token))
        finished = pda.run_step(json_grammar, random_token)
        if finished:
            break
    if not finished:
        return complete_partial_json(pda.data, pda.stack)
    else:
        return pda.data

class Closeability(Enum):
    MUST_NOT_CLOSE = 1
    MAY_CLOSE = 2
    MUST_CLOSE = 3
    NA = 4

json_obj_begin = set(JSONToken.NULL, JSONToken.BOOL_T, JSONToken.BOOL_F, JSONToken.NUM, JSONToken.STR, JSONToken.LEFT_CURLY_BRACKET, JSONToken.LEFT_SQUARE_BRACKET)

def derive_valid_object(schema_context_frame, cur_state):
    pass #TODO

def derive_list_state(schema_context_frame):
    pass #TODO

def derive_dict_state(schema_context_frame):
    pass #TODO

def filter_token_by_schema(next_token_candidates : list[JSONToken], schema_context_frame, cur_state : int):
    filtered_tokens = set(next_token_candidates)
    closeability_status = Closeability.NA
    # Beginning of next object
    if cur_state in (0, 1, 4):
        valid_obj_token = derive_valid_object(schema_context_frame, cur_state)
        invalid_obj_begin = json_obj_begin - set(valid_obj_token)
        filtered_tokens = filtered_tokens - invalid_obj_begin
    # Control list closable/must-close
    if cur_state in (1, 2):
        closeability_status = derive_list_state(schema_context_frame)
    # Control dict closable/must-close
    if cur_state in (3, 5):
        closeability_status = derive_dict_state(schema_context_frame)
    # Filter the close brackets
    if closeability_status == Closeability.MUST_NOT_CLOSE:
        filtered_tokens = filtered_tokens - set(JSONToken.RIGHT_CURLY_BRACKET, JSONToken.RIGHT_SQUARE_BRACKET)
    if closeability_status == Closeability.MUST_CLOSE:
        if cur_state in (1, 2):
            filtered_tokens = set(JSONToken.RIGHT_SQUARE_BRACKET)
        elif cur_state in (3, 5):
            filtered_tokens = set(JSONToken.RIGHT_CURLY_BRACKET)
        else:
            raise ValueError("Internal error")
    #TODO gen dict key value exactly
    return list(filtered_tokens)

def update_schema_context(schema_context, selected_token, cur_state):
    pass

def gen_json_schema(schema):
    pda = PDA()
    finished = False
    schema_context = [(schema, None)]
    while not finished:
        # Get valid tokens
        next_token_candidates = pda.get_valid_next_token(json_grammar)
        # Filter by schema context
        valid_next_tokens = filter_token_by_schema(next_token_candidates, schema_context[-1], pda.state)
        # Random sample for now
        random_token = gen_json_token(random.choice(valid_next_tokens))
        # Update schema context
        update_schema_context(schema_context, random_token, pda.state)
        # Run PDA
        finished = pda.run_step(json_grammar, random_token)
    return pda.data

product_schema1 = {
    "type": "object",
    "properties": {
        "id" : { "type": "number" },
        "name" : { "type": "string" },
        "details": {
            "type": "object",
            "properties": {
                "manufactorer": { "type": "string" },
                "year": { "type": "number" },
                "description": { "type": "string" }
            },
            "required": ["manufactorer"]
        },
        "reviews": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "reviewer": { "type": "string" },
                    "rating": { "type": "number" },
                    "comment": { "type": "string" }
                },
                "required": ["reviewer", "rating"]
            }
        },
        "tags" : { "type": "array", "items": { "type": "string" }, "minItems": 1, "maxItems": 3 }
    },
    "required": ["id", "name", "details"]
}



if __name__ == "__main__":
    for i in range(5):
        print(random_json(random.randint(20, 120)))
    for i in range(3):
        print(gen_json_schema(product_schema1))
