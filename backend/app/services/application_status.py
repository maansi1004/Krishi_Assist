"""The only application states a farmer can set (the same 7 as in the project report)."""
from typing import Literal, get_args

ApplicationStatus = Literal[
    "Planning",
    "Documents Pending",
    "Applied",
    "Under Verification",
    "Approved",
    "Rejected",
    "Completed",
]
APPLICATION_STATUSES: list[str] = list(get_args(ApplicationStatus))
