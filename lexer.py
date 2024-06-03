import copy

print("Lexer")

class FSM:
    def __init__(self, state_transitions, character_class, init_state, accept_state, callback) -> None:
        self.state_transitions = state_transitions
        self.character_class = character_class
        self.state = init_state # Notice this
        self.accept_state = accept_state
        self.callback = callback
    
    def run_step(self, c):
        cur_state = self.state
        routes = self.state_transitions[self.state]
        matched = False
        accept = False
        for route in routes:
            (character_class_label, next_state) = route
            character_class_tester = self.character_class[character_class_label]
            if character_class_tester.belongs(c):
                # Matched route - update state + callback
                matched = True
                self.state = next_state
                if self.state == self.accept_state:
                    accept = True
                self.callback.state_transit(c, character_class_label, cur_state, next_state, accept)
                break
        return (matched, accept)


# Strategy 1 - everything brute force?
def filter_token_compatibility_bruteforce(fsm, token_map):
    result = {}
    for token_id, s in token_map.items():
        new_fsm = copy.copy(fsm)
        success = True
        accept = None
        for c in s:
            matched, accept = new_fsm.run_step(c)
            if not matched:
                success = False
                break
        if success:
            result[token_id] = (new_fsm.state, accept)
    return result
