VALID_TRANSITIONS = {
    'pending': ['processing'],
    'processing': ['completed', 'failed'],
    'completed': [],
    'failed': [],
}

def transition_payout(payout, new_status):
    """Validate and perform a state transition for a payout.
    Raises ValueError if the transition is illegal.
    """
    current = payout.status
    allowed = VALID_TRANSITIONS.get(current, [])
    if new_status not in allowed:
        raise ValueError(f'Invalid transition from {current} to {new_status}')
    payout.status = new_status
    payout.save(update_fields=['status', 'updated_at'])
