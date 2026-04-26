"""
Centralized State Machine Logic for KYC Submissions
All state transitions are defined here.
"""

from enum import Enum
from datetime import datetime


class SubmissionStatus(Enum):
    DRAFT = 'draft'
    SUBMITTED = 'submitted'
    UNDER_REVIEW = 'under_review'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    MORE_INFO_REQUESTED = 'more_info_requested'


# Define allowed transitions
ALLOWED_TRANSITIONS = {
    SubmissionStatus.DRAFT.value: [
        SubmissionStatus.SUBMITTED.value,
    ],
    SubmissionStatus.SUBMITTED.value: [
        SubmissionStatus.UNDER_REVIEW.value,
    ],
    SubmissionStatus.UNDER_REVIEW.value: [
        SubmissionStatus.APPROVED.value,
        SubmissionStatus.REJECTED.value,
        SubmissionStatus.MORE_INFO_REQUESTED.value,
    ],
    SubmissionStatus.MORE_INFO_REQUESTED.value: [
        SubmissionStatus.SUBMITTED.value,
    ],
    SubmissionStatus.APPROVED.value: [],
    SubmissionStatus.REJECTED.value: [],
}


class StateTransitionError(Exception):
    """Exception raised when an illegal state transition is attempted."""
    pass


def validate_transition(current_status, new_status):
    """
    Validate if a transition from current_status to new_status is allowed.
    
    Args:
        current_status (str): Current submission status
        new_status (str): Desired new status
        
    Raises:
        StateTransitionError: If transition is not allowed
        
    Returns:
        bool: True if transition is valid
    """
    if current_status not in ALLOWED_TRANSITIONS:
        raise StateTransitionError(f"Unknown status: {current_status}")
    
    if new_status not in ALLOWED_TRANSITIONS:
        raise StateTransitionError(f"Unknown status: {new_status}")
    
    if new_status not in ALLOWED_TRANSITIONS[current_status]:
        allowed = ', '.join(ALLOWED_TRANSITIONS[current_status]) or 'none'
        raise StateTransitionError(
            f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Allowed transitions: {allowed}"
        )
    
    return True


def get_allowed_transitions(current_status):
    """Get list of allowed transitions from current status."""
    if current_status not in ALLOWED_TRANSITIONS:
        return []
    return ALLOWED_TRANSITIONS[current_status]
