"""
src/engine/adjustment_engine.py
===============================
Manages salary adjustment proposals, recommended compensation ranges,
governance approval workflows, and immutable audit trails.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd


class ProposalStateMachine:
    """
    Enforces valid lifecycle state transitions for salary adjustment proposals.
    Rules:
    - Only Manager can approve/reject at Manager stage.
    - Only HR Partner can approve/reject at HR stage.
    - Proposal can only reach IMPLEMENTED after both Manager and HR have APPROVED.
    - Withdrawn can occur at any stage before implementation.
    """

    VALID_TRANSITIONS = {
        "OPEN": ["PENDING_MANAGER", "WITHDRAWN"],
        "PENDING_MANAGER": ["MANAGER_APPROVED", "MANAGER_REJECTED", "WITHDRAWN"],
        "MANAGER_APPROVED": ["PENDING_HR", "WITHDRAWN"],
        "MANAGER_REJECTED": ["WITHDRAWN", "OPEN"],
        "PENDING_HR": ["HR_APPROVED", "HR_REJECTED", "WITHDRAWN"],
        "HR_REJECTED": ["PENDING_MANAGER", "WITHDRAWN"],
        "HR_APPROVED": ["IMPLEMENTED", "WITHDRAWN"],
        "IMPLEMENTED": [],  # Terminal state
        "WITHDRAWN": [],    # Terminal state
    }

    @classmethod
    def transition(
        cls,
        proposal: Dict,
        target_state: str,
        actor_id: str,
        actor_role: str,
        notes: str = "",
    ) -> Tuple[Dict, Dict]:
        """
        Transition proposal to target_state.
        Returns: (updated_proposal, audit_event_record)
        Raises ValueError if transition is unauthorized or invalid.
        """
        current_state = proposal.get("final_status", "OPEN")
        allowed = cls.VALID_TRANSITIONS.get(current_state, [])

        if target_state not in allowed:
            raise ValueError(
                f"Invalid transition: Cannot move proposal from '{current_state}' to '{target_state}'. "
                f"Allowed target states: {allowed}"
            )

        # Role-based governance enforcement
        if target_state in ("MANAGER_APPROVED", "MANAGER_REJECTED") and actor_role not in ("MANAGER", "ADMIN"):
            raise ValueError("Only a Manager or Administrator can grant Manager Approval.")

        if target_state in ("HR_APPROVED", "HR_REJECTED") and actor_role not in ("HR_PARTNER", "ADMIN"):
            raise ValueError("Only an HR Business Partner or Administrator can grant HR Approval.")

        if target_state == "IMPLEMENTED":
            if proposal.get("manager_approval") != "APPROVED":
                raise ValueError("Cannot implement proposal: Manager approval is missing or pending.")
            if proposal.get("hr_approval") != "APPROVED":
                raise ValueError("Cannot implement proposal: Mandatory HR Partner approval is missing.")

        now_iso = datetime.now().isoformat()
        updated = proposal.copy()
        updated["final_status"] = target_state
        updated["updated_at"] = now_iso

        if target_state == "MANAGER_APPROVED":
            updated["manager_approval"] = "APPROVED"
            updated["manager_approval_date"] = now_iso[:10]
            # Advance to HR review automatically
            updated["final_status"] = "PENDING_HR"
        elif target_state == "MANAGER_REJECTED":
            updated["manager_approval"] = "REJECTED"
            updated["manager_approval_date"] = now_iso[:10]
        elif target_state == "HR_APPROVED":
            updated["hr_approval"] = "APPROVED"
            updated["hr_approval_date"] = now_iso[:10]
        elif target_state == "HR_REJECTED":
            updated["hr_approval"] = "REJECTED"
            updated["hr_approval_date"] = now_iso[:10]

        audit_event = {
            "proposal_id": proposal.get("proposal_id"),
            "timestamp": now_iso,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "from_state": current_state,
            "to_state": updated["final_status"],
            "notes": notes,
        }

        return updated, audit_event


class ProposalAuditTrail:
    """Maintains an append-only, in-memory or persisted log of proposal governance events."""

    def __init__(self):
        self.events: List[Dict] = []

    def record(self, event: Dict) -> None:
        self.events.append(event)

    def get_history(self, proposal_id: str) -> List[Dict]:
        return [e for e in self.events if e.get("proposal_id") == proposal_id]

    def to_dataframe(self) -> pd.DataFrame:
        if not self.events:
            return pd.DataFrame(columns=[
                "proposal_id", "timestamp", "actor_id", "actor_role",
                "from_state", "to_state", "notes"
            ])
        return pd.DataFrame(self.events)


def calculate_recommended_adjustment(
    current_salary: float,
    band_min: float,
    band_mid: float,
    band_max: float,
    perf_rating: float = 3.0,
    peer_median: Optional[float] = None,
) -> Dict[str, float]:
    """
    Calculate proposed salary adjustment range based on compensation band and performance:
    - Min target: band_min
    - Target: bring towards band midpoint (scaled by performance: higher rating -> higher target)
    - Max target: min(band_mid * 1.05, band_max)
    """
    if perf_rating >= 4.5:
        target_ratio = 1.00  # Target full band midpoint
    elif perf_rating >= 3.5:
        target_ratio = 0.95  # Target 95% of midpoint
    elif perf_rating >= 2.5:
        target_ratio = 0.90  # Target 90% of midpoint
    else:
        target_ratio = 0.85  # Target 85% of midpoint

    recommended_salary = max(current_salary, band_mid * target_ratio)
    if peer_median and peer_median > 0:
        # Also anchor against comparable peer median
        recommended_salary = max(recommended_salary, min(peer_median * 0.95, band_mid))

    prop_min = max(current_salary, band_min)
    prop_max = max(recommended_salary * 1.05, band_mid)

    change_pct = ((recommended_salary - current_salary) / current_salary) * 100 if current_salary > 0 else 0.0

    return {
        "current_salary": round(current_salary, 2),
        "proposed_salary_min": round(prop_min, 2),
        "proposed_salary_max": round(prop_max, 2),
        "proposed_salary_recommended": round(recommended_salary, 2),
        "proposed_change_pct": round(change_pct, 2),
    }
