import random

first_names = ('John', 'Andy', 'Joe', 'Harry', 'Peter', 'Sam')
last_names = ('Johnson', 'Smith', 'Williams', 'Jackson', 'Harris')

def random_name() -> str:
    return random.choice(first_names) + " " + random.choice(last_names)
