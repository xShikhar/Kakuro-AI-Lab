"""Event-sourced domain reconstruction and deterministic, audience-specific explanations."""
import copy


def snapshot(domains):
    """Serialize domains in stable order so traces can be replayed without running a solver."""
    return {k: sorted(v) for k, v in domains.items()}


def replay(trace, index):
    """Reconstruct the board after event index; backtrack snapshots restore complete state."""
    state = {}
    for event in trace[:index + 1]:
        if event.get('snapshot') is not None:
            state = copy.deepcopy(event['snapshot'])
        else:
            state.update(copy.deepcopy(event.get('after', {})))
    return state


def explain(event, level='Technical'):
    """Translate a real operation for beginners, technical readers or research inspection."""
    if level == 'Research':
        return f"{event['type']}: {event['reason']} | scopes={event.get('runs', [])}; before={event.get('before', {})}; after={event.get('after', {})}"
    if level == 'Beginner':
        return event.get('friendly', event['reason'])
    return event['reason']
