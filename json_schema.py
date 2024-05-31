from typing import Optional
from basic_parse import *

import random
from enum import Enum

from util import *

print("Random select")

def gen_json_token(token_type : JSONToken, constraint: Optional[dict]) -> GrammarToken:
    val = None
    if constraint is not None:
        if constraint["type"] == 0:
            val = constraint["value"]
        else:
            raise ValueError("Unknown constraint type")
    else:
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
        random_token = gen_json_token(*[random.choice(possible_next_token), None])
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

class DictSelectPhase(Enum):
    REQUIRED = 1
    OPTIONAL = 2
    EXHAUSTED = 3

json_obj_begin = set([JSONToken.NULL, JSONToken.BOOL_T, JSONToken.BOOL_F, JSONToken.NUM, JSONToken.STR, JSONToken.LEFT_CURLY_BRACKET, JSONToken.LEFT_SQUARE_BRACKET])

jsontype_token_map = {
    "null": [JSONToken.NULL],
    "boolean": [JSONToken.BOOL_F, JSONToken.BOOL_T],
    "number": [JSONToken.NUM],
    "string": [JSONToken.STR],
    "array": [JSONToken.LEFT_SQUARE_BRACKET],
    "object": [JSONToken.LEFT_CURLY_BRACKET]
}

def derive_valid_object(schema_context_frame, cur_state):
    (schema, context) = schema_context_frame
    # Start state
    if cur_state == 0:
        return jsontype_token_map[schema["type"]]
    # List
    if cur_state == 1:
        return jsontype_token_map[schema["items"]["type"]]
    # Object
    if cur_state == 4:
        cur_property = context["cur_property"]
        return jsontype_token_map[schema["properties"][cur_property]["type"]]

def derive_list_state(schema_context_frame):
    minItems = schema_context_frame[0]["minItems"]
    maxItems = schema_context_frame[0]["maxItems"]
    curItems = schema_context_frame[1]["curItems"]
    if minItems is not None and curItems < minItems:
        return Closeability.MUST_NOT_CLOSE
    if maxItems is not None and curItems == maxItems:
        return Closeability.MUST_CLOSE
    return Closeability.MAY_CLOSE

def derive_dict_state(schema_context_frame):
    #DONE (required prop => optional prop => exhausted prop)
    #return random.choice([Closeability.MAY_CLOSE, Closeability.MUST_CLOSE, Closeability.MUST_NOT_CLOSE])
    phase = schema_context_frame[1]["select"]["phase"]
    if phase == DictSelectPhase.REQUIRED:
        return Closeability.MUST_NOT_CLOSE
    elif phase == DictSelectPhase.OPTIONAL:
        return Closeability.MAY_CLOSE
    elif phase == DictSelectPhase.EXHAUSTED:
        return Closeability.MUST_CLOSE
    else:
        raise ValueError("Unknown phase")

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
        filtered_tokens = filtered_tokens - set([JSONToken.RIGHT_CURLY_BRACKET, JSONToken.RIGHT_SQUARE_BRACKET])
    if closeability_status == Closeability.MUST_CLOSE:
        if cur_state in (1, 2):
            filtered_tokens = set([JSONToken.RIGHT_SQUARE_BRACKET])
        elif cur_state in (3, 5):
            filtered_tokens = set([JSONToken.RIGHT_CURLY_BRACKET])
        else:
            raise ValueError("Internal error")
    #DONE gen dict key value exactly
    if cur_state == 3:
        filtered_tokens = filtered_tokens - set([JSONToken.STR])
        filtered_tokens = [(tok, None) for tok in filtered_tokens]
        constraint = { "type": 0, "value": schema_context_frame[1]["cur_property"] }
        filtered_tokens.append((JSONToken.STR, constraint))
    else:
        filtered_tokens = [(tok, None) for tok in filtered_tokens]
    return filtered_tokens

def init_list_context(schema_context):
    schema = schema_context[-1][0]
    schema_context[-1][1] = {}
    if schema["minItems"] is not None:
        schema_context[-1][1]["minItems"] = schema["minItems"]
    if schema["maxItems"] is not None:
        schema_context[-1][1]["maxItems"] = schema["maxItems"]
    schema_context[-1][1]["curItems"] = 0

def init_map_context(schema_context):
    schema = schema_context[-1][0]
    schema_context[-1][1] = {}
    all_properties = schema["properties"].keys()
    required_properties = schema["required"]
    optional_properties = list(set(all_properties) - set(required_properties))
    schema_context[-1][1]["required_properties"] = required_properties
    schema_context[-1][1]["optional_properties"] = optional_properties
    select = {}
    if len(required_properties) > 0:
        select = {
            "phase": DictSelectPhase.REQUIRED,
            "i": 0
        }
    elif len(optional_properties) > 0:
        select = {
            "phase": DictSelectPhase.OPTIONAL,
            "used": set()
        }
    else:
        select = {
            "phase": DictSelectPhase.EXHAUSTED
        }
    schema_context[-1][1]["select"] = select
    schema_context[-1][1]["cur_property"] = None

#DONE
def advance_property_target(schema_state):
    cur_property = schema_state["cur_property"]
    select = schema_state["select"]
    required_properties = schema_state["required_properties"]
    optional_properties = schema_state["optional_properties"]

    if select["phase"] == DictSelectPhase.REQUIRED:
        if select["i"] == len(required_properties) - 1:
            if len(optional_properties) > 0:
                new_select = {
                    "phase": DictSelectPhase.OPTIONAL,
                    "used": set()
                }
            else:
                new_select = {
                    "phase": DictSelectPhase.EXHAUSTED
                }
        else:
            new_select = select
            new_select["i"] += 1
    elif select["phase"] == DictSelectPhase.OPTIONAL:
        new_select = select
        new_select["used"].union({ cur_property })
        if len(new_select["used"]) == len(optional_properties):
            new_select = {
                "phase": DictSelectPhase.EXHAUSTED
            }
    else:
        raise ValueError("shouldn't be exhausted here")
    schema_state["select"] = new_select
    schema_state["cur_property"] = None

#TODO prev state
def update_schema_context(schema_context, selected_token, prev_state, cur_state):
    # Descend to subobject
    if selected_token.type == JSONToken.LEFT_SQUARE_BRACKET.value:
        if prev_state == 1:
            cur_schema = schema_context[-1][0]
            sub_schema = cur_schema["items"]
            schema_context.append([sub_schema, None])
        init_list_context(schema_context)
    if selected_token.type == JSONToken.LEFT_CURLY_BRACKET.value:
        if prev_state == 4:
            cur_schema = schema_context[-1][0]
            cur_property = schema_context[-1][1]["cur_property"]
            sub_schema = cur_schema["properties"][cur_property]
            schema_context.append([sub_schema, None])
        init_map_context(schema_context)
    # Ascend
    if selected_token.type in [JSONToken.RIGHT_CURLY_BRACKET.value, JSONToken.RIGHT_SQUARE_BRACKET.value]:
        schema_context.pop()
    # Update object state
    if cur_state == 2:
        schema_context[-1][1]["curItems"] += 1
    if cur_state == 5:
        advance_property_target(schema_context[-1][1])
    # Selected dict key (state 3 -> 6(intermediate dummy))
    if cur_state == 6:
        schema_context[-1][1]["cur_property"] = selected_token.value

def gen_json_schema(schema):
    pda = PDA()
    finished = False
    init = True
    prev_state = None
    schema_context = [[schema, None]]
    while not finished:
        if not init:
            # Update schema context
            update_schema_context(schema_context, random_token, prev_state, pda.state)
        # Get valid tokens
        next_token_candidates = pda.get_valid_next_token(json_grammar)
        # Filter by schema context
        valid_next_tokens = filter_token_by_schema(next_token_candidates, schema_context[-1], pda.state)
        # Random sample for now
        random_token = gen_json_token(*random.choice(valid_next_tokens))
        # Run PDA
        prev_state = pda.state
        finished = pda.run_step(json_grammar, random_token)
        init = False
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
    print("Test 1 - random gen JSON")
    for i in range(5):
        print(random_json(random.randint(20, 120)))
    print("Test 2 - unit test filter_token_by_schema")
    pda = PDA()
    pda.state = 0
    print(filter_token_by_schema(pda.get_valid_next_token(json_grammar), (product_schema1, None), 0))
    #pda.state = 3
    #print(filter_token_by_schema(pda.get_valid_next_token(json_grammar), (product_schema1, None), 3))
    pda.state = 4
    print(filter_token_by_schema(pda.get_valid_next_token(json_grammar), (product_schema1, {"cur_property": "name"}), 4))
    pda.state = 4
    print(filter_token_by_schema(pda.get_valid_next_token(json_grammar), (product_schema1, {"cur_property": "reviews"}), 4))
    pda.state = 1
    print(filter_token_by_schema(pda.get_valid_next_token(json_grammar), (product_schema1["properties"]["tags"], {"curItems": 3}), 1))
    pda.state = 1
    print(filter_token_by_schema(pda.get_valid_next_token(json_grammar), (product_schema1["properties"]["tags"], {"curItems": 2}), 1))
    pda.state = 1
    print(filter_token_by_schema(pda.get_valid_next_token(json_grammar), (product_schema1["properties"]["tags"], {"curItems": 0}), 1))
    print("Test 3 - gen by JSON Schema")
    for i in range(3):
        print(gen_json_schema(product_schema1))
