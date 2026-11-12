"""Independent finite-domain proof checker. It imports no solver or technique implementation."""
from .replay import replay
from ..core.model import Board


def enumerate_premise(constraint, domains):
    """Brute-force a clue's injective assignments, using arithmetic bounds only to skip dead prefixes."""
    cells, target = constraint['cells'], constraint['target']
    tuples, values = [], []

    def enumerate_prefix(i, total):
        """Visit every distinct assignment consistent with the stated domains and sum."""
        if i == len(cells):
            if total == target:
                tuples.append(tuple(values))
            return
        rest = [set(domains[k]) - set(values) for k in cells[i:]]
        if any(not d for d in rest) or total + sum(min(d) for d in rest) > target or total + sum(max(d) for d in rest) < target:
            return
        for digit in sorted(rest[0]):
            values.append(digit)
            enumerate_prefix(i + 1, total + digit)
            values.pop()

    enumerate_prefix(0, 0)
    return tuples


def verify_proof(proof):
    """Accept reductions only if independent enumeration eliminates every removed value.

    Local arc consistency is a sound but incomplete entailment procedure. Certificates
    may keep extra values; they may never delete a value which still has support.
    """
    try:
        stated = proof['premises']['domains']
        domains = {k: set(v) for k, v in stated.items()}
        if any(any(type(v) is not int or not 1 <= v <= 9 for v in d) for d in stated.values()):
            return False
        constraints = proof['premises']['constraints']
        while True:
            changed = False
            for constraint in constraints:
                tuples = enumerate_premise(constraint, domains)
                for i, k in enumerate(constraint['cells']):
                    remaining = domains[k] & {t[i] for t in tuples}
                    if remaining != domains[k]:
                        domains[k] = remaining
                        changed = True
            if not changed:
                break
        conclusion = proof['conclusion']
        return bool(conclusion) and all(k in domains and set(v) <= set(stated[k]) and domains[k] <= set(v) for k, v in conclusion.items())
    except (KeyError, TypeError, ValueError):
        return False


def verify_trace(puzzle, trace, givens=None):
    """Validate the full state machine and local certificates, keeping guesses explicitly conditional.

    Initialization must match supplied givens; branches push the parent, restores
    pop that exact parent, and solved snapshots must satisfy the original board.
    Forced assignments are redundant singleton announcements after a verified
    reduction, never permission to mutate state without a certificate.
    """
    board = Board(puzzle)
    givens=givens or {}
    board.validate_entries(givens)
    valid_constraints = {r.id: {'id': r.id, 'cells': list(r.cells), 'target': r.target} for r in board.runs}
    state, verified, total, failures = {}, 0, 0, []
    assumptions,stack,last_reduction,last_branch=0,[],{},None
    for index,event in enumerate(trace):
        kind=event.get('type')
        deduction=kind in ('technique_applied','eliminate_candidate') or kind=='assign' and event.get('forced')
        total+=int(deduction)
        valid=event.get('step')==index
        after=event.get('after',{})
        try:
            if kind=='domain_init':
                expected={k:[givens[k]] if k in givens else list(range(1,10)) for k in board.variables}
                valid=valid and index==0 and event.get('snapshot')==expected and not after
            elif not state:
                valid=False
            elif kind in ('technique_applied','eliminate_candidate'):
                proof=event.get('justification')
                if kind=='eliminate_candidate':
                    constraints=[valid_constraints[r] for r in event.get('runs',[])]
                    scope=set().union(*(set(c['cells']) for c in constraints))
                    proof={'premises':{'domains':{k:state[k] for k in scope},'constraints':constraints},'conclusion':after}
                premises=proof.get('premises',{}) if proof else {}
                valid=valid and bool(premises.get('constraints')) and bool(after)
                valid=valid and all(state.get(k)==v for k,v in premises.get('domains',{}).items())
                valid=valid and all(valid_constraints.get(c.get('id'))==c for c in premises.get('constraints',[]))
                valid=valid and all(event.get('before',{}).get(k)==state.get(k) for k in after)
                valid=valid and proof.get('conclusion')==after and verify_proof(proof)
                if valid:
                    last_reduction=dict(after)
            elif kind=='branch':
                valid=valid and len(after)==1 and all(len(v)==1 and v[0] in state.get(k,[]) and event.get('before',{}).get(k)==state.get(k) for k,v in after.items())
                if valid:
                    stack.append({k:list(v) for k,v in state.items()})
                    assumptions+=1
                    last_branch=dict(after)
                    last_reduction={}
            elif kind=='assign':
                valid=valid and bool(after) and all(len(v)==1 and state.get(k)==v for k,v in after.items())
                origin=last_reduction if event.get('forced') else last_branch or {}
                valid=valid and all(origin.get(k)==v for k,v in after.items())
            elif kind=='backtrack':
                valid=valid and bool(stack) and event.get('snapshot')==stack[-1] and not after
                if valid:
                    stack.pop();last_reduction={};last_branch=None
            elif kind=='solved':
                snap=event.get('snapshot',{})
                valid=valid and snap==state and all(len(v)==1 for v in snap.values()) and board.valid_solution({k:v[0] for k,v in snap.items()}) and not after
            elif kind in ('constraint_eval','heuristic_select','contradiction'):
                valid=valid and not after and 'snapshot' not in event
            else:
                valid=False
            if kind not in ('domain_init','backtrack','solved') and 'snapshot' in event:
                valid=False
        except (KeyError,TypeError,ValueError,AttributeError,IndexError):
            valid=False
        if valid:
            verified+=int(deduction)
            if 'snapshot' in event:
                state={k:list(v) for k,v in event['snapshot'].items()}
            else:
                state.update({k:list(v) for k,v in after.items()})
        else:
            failures.append(event.get('step',index))
    return dict(verified=verified,total=total,failures=failures,assumptions=assumptions,valid=bool(trace) and not failures)
