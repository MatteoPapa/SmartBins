import itertools, pickle
from tqdm import tqdm
from config import N_BINS, DISCRETIZATION, MAX_FILL, COLLECTION_COST, OVERFLOW_PENALTY, MAX_INCREMENT

STATES  = list(range(0, MAX_FILL + DISCRETIZATION, DISCRETIZATION))
ACTIONS = ['wait'] + [f'collect_{i}' for i in range(N_BINS)]

def build_single_trans():
    trans = {}
    D = DISCRETIZATION
    K = MAX_INCREMENT
    denom = (K + 1) * D
    s_part = sum(max(0, D - k) for k in range(K + 1))
    for b in STATES:
        probs = {}
        if b == MAX_FILL:
            probs[b] = 1.0
        else:
            p_stay = s_part / denom
            p_up   = 1.0 - p_stay
            b_up   = min(b + D, MAX_FILL)
            probs[b]   = p_stay
            probs[b_up] = probs.get(b_up, 0) + p_up
        trans[b] = probs
    return trans

SINGLE_TRANS = build_single_trans()

def reward(state, action, next_state):
    pen = sum(OVERFLOW_PENALTY for v in next_state if v > 95)
    if action != 'wait':
        pen -= COLLECTION_COST
    return pen

def get_transitions(state, action):
    if action == 'wait':
        per_bin = [SINGLE_TRANS[s] for s in state]
        lists = [list(d.items()) for d in per_bin]
        for combo in itertools.product(*lists):
            ns = tuple(c[0] for c in combo)
            p  = 1.0
            for _, pi in combo: p *= pi
            yield ns, p
    else:
        idx = int(action.split('_')[1])
        ns = list(state); ns[idx] = 0
        yield tuple(ns), 1.0

def value_iteration(gamma=0.99, theta=1e-4):
    all_states = list(itertools.product(STATES, repeat=N_BINS))
    V = {s: 0.0 for s in all_states}
    policy = {s: 'wait' for s in all_states}
    it = 0
    while True:
        delta = 0.0
        for s in tqdm(all_states, desc=f"Iter {it+1}", leave=False):
            v_old = V[s]
            # wait
            q_best = -1e18
            a_best = None
            q_wait = 0.0
            for s2, p in get_transitions(s, 'wait'):
                q_wait += p * (reward(s, 'wait', s2) + gamma * V[s2])
            q_best, a_best = q_wait, 'wait'
            # collects
            for a in ACTIONS[1:]:
                (s2, p) = next(get_transitions(s, a))
                q = p * (reward(s, a, s2) + gamma * V[s2])
                if q > q_best:
                    q_best, a_best = q, a
            V[s] = q_best
            policy[s] = a_best
            delta = max(delta, abs(v_old - q_best))
        it += 1
        if delta < theta:
            print(f"Converged in {it} iterations (delta={delta:.6f})")
            break
    return V, policy

def save_results(V, policy, vf_path="value_function.pkl", p_path="policy.pkl"):
    with open(vf_path, "wb") as f: pickle.dump(V, f)
    with open(p_path, "wb") as f: pickle.dump(policy, f)
    print("Saved.")

if __name__ == '__main__':
    V, policy = value_iteration()
    save_results(V, policy)
    for s in [(0,)*N_BINS, (MAX_FILL,)*N_BINS]:
        print(f"{s} -> {policy[s]}  V={V[s]:.3f}")
