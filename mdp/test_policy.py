import random
import pickle
import numpy as np
from config import N_BINS, DISCRETIZATION, MAX_FILL, COLLECTION_COST, OVERFLOW_PENALTY, MAX_INCREMENT
from itertools import product

# --- Load and helper functions ---

def load_results(vf_path="value_function.pkl", p_path="policy.pkl"):
    """Ricarica V e policy da file pickle."""
    with open(vf_path, "rb") as vf_file:
        V = pickle.load(vf_file)
    with open(p_path, "rb") as p_file:
        policy = pickle.load(p_file)
    return V, policy


def quantize_state(continuous_state):
    """
    Porta ogni valore di fill al livello discreto più vicino:
    round(x/D)*D, poi clip in [0, MAX_FILL].
    """
    discrete = []
    for x in continuous_state:
        d = round(x / DISCRETIZATION) * DISCRETIZATION
        d = min(max(d, 0), MAX_FILL)
        discrete.append(d)
    return tuple(discrete)


def get_transitions(state, action, SINGLE_TRANS, N_BINS):
    """Riproduce la logica di transizione del MDP."""
    if action == 'wait':
        per_bin = [SINGLE_TRANS[s] for s in state]
        for prod in product(*[list(d.keys()) for d in per_bin]):
            prob = np.prod([per_bin[i][v] for i, v in enumerate(prod)])
            yield tuple(prod), prob
    else:
        idx = int(action.split('_')[1])
        new_state = list(state)
        new_state[idx] = 0
        yield tuple(new_state), 1.0


def reward(state, action, next_state):
    """
    Reward = sum of overflow penalties for any bin beyond 95% in next_state,
    minus collection cost if action is a collect.
    """
    r = 0.0
    for fill in next_state:
        if fill > 95:
            r += OVERFLOW_PENALTY
    if action != 'wait':
        r -= COLLECTION_COST
    return r

# Precompute SINGLE_TRANS for debug logic
levels = list(range(0, MAX_FILL + DISCRETIZATION, DISCRETIZATION))
SINGLE_TRANS = {s: {} for s in levels}
p = 1.0 / (MAX_INCREMENT + 1)
for s in levels:
    for k in range(MAX_INCREMENT + 1):
        nxt = min(s + k * DISCRETIZATION, MAX_FILL)
        SINGLE_TRANS[s][nxt] = SINGLE_TRANS[s].get(nxt, 0) + p

# Build action list
actions = ['wait'] + [f'collect_{i}' for i in range(N_BINS)]

# --- Random continuous tests ---

def random_continuous_tests(n_samples=10):
    V, policy = load_results()
    print(f"Verifico {n_samples} stati casuali (continui → discrete):\n")
    for i in range(n_samples):
        cont = [random.uniform(0, MAX_FILL) for _ in range(N_BINS)]
        disc = quantize_state(cont)
        action = policy.get(disc, None)
        print(f"{i+1:2d}) cont=({', '.join(f'{x:.1f}' for x in cont)})",
              f"→ disc={disc} → action={action}")
    # Esempio di debug per uno stato particolare:
    debug_state = (0, 60, 40, 80, 20)
    print("\n--- Debug Q-values per lo stato", debug_state, "---")
    for a in actions:
        q = 0.0
        for ns, prob in get_transitions(debug_state, a, SINGLE_TRANS, N_BINS):
            r = reward(debug_state, a, ns)
            q += prob * (r + 0.99 * V[ns])
        print(f"Q({a}): {q:.6f}")

if __name__ == "__main__":
    random.seed(123)
    random_continuous_tests(80)
