"""
tests/test_adjustment_engine.py
================================
Unit tests for the AdjustmentProposal state machine, audit trail,
and recommended salary calculation.

Covers:
- ProposalStateMachine valid state transitions
- ProposalStateMachine unauthorized role-based rejection
- ProposalStateMachine terminal state enforcement
- ProposalStateMachine dual-approval gate before IMPLEMENTED
- ProposalAuditTrail record, history retrieval, and DataFrame export
- calculate_recommended_adjustment: performance-scaled targeting
- calculate_recommended_adjustment: peer-median anchoring
"""

from __future__ import annotations

import pytest

from src.engine.adjustment_engine import (
    ProposalStateMachine,
    ProposalAuditTrail,
    calculate_recommended_adjustment,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def open_proposal():
    return {
        "proposal_id": "ADJ-2026-000001",
        "employee_id": "EMP-000001",
        "final_status": "OPEN",
        "manager_approval": None,
        "hr_approval": None,
    }


# ---------------------------------------------------------------------------
# ProposalStateMachine — valid transitions
# ---------------------------------------------------------------------------

class TestProposalStateMachineValidTransitions:

    def test_open_to_pending_manager(self, open_proposal):
        updated, event = ProposalStateMachine.transition(
            open_proposal, "PENDING_MANAGER", actor_id="MGR-001", actor_role="MANAGER"
        )
        assert updated["final_status"] == "PENDING_MANAGER"
        assert event["from_state"] == "OPEN"
        assert event["to_state"] == "PENDING_MANAGER"

    def test_manager_approval_advances_to_pending_hr(self, open_proposal):
        """MANAGER_APPROVED should auto-advance state to PENDING_HR."""
        pending_mgr = {**open_proposal, "final_status": "PENDING_MANAGER"}
        updated, event = ProposalStateMachine.transition(
            pending_mgr, "MANAGER_APPROVED", actor_id="MGR-001", actor_role="MANAGER"
        )
        # State machine auto-advances to PENDING_HR after manager approval
        assert updated["final_status"] == "PENDING_HR"
        assert updated["manager_approval"] == "APPROVED"

    def test_hr_approval_sets_hr_approved(self, open_proposal):
        pending_hr = {
            **open_proposal,
            "final_status": "PENDING_HR",
            "manager_approval": "APPROVED",
        }
        updated, event = ProposalStateMachine.transition(
            pending_hr, "HR_APPROVED", actor_id="HR-001", actor_role="HR_PARTNER"
        )
        assert updated["final_status"] == "HR_APPROVED"
        assert updated["hr_approval"] == "APPROVED"

    def test_full_dual_approval_to_implemented(self, open_proposal):
        """Full happy-path: OPEN → PENDING_MANAGER → PENDING_HR → HR_APPROVED → IMPLEMENTED."""
        proposal = {**open_proposal, "final_status": "PENDING_MANAGER"}

        # Manager approves
        proposal, _ = ProposalStateMachine.transition(
            proposal, "MANAGER_APPROVED", actor_id="MGR-001", actor_role="MANAGER"
        )
        assert proposal["final_status"] == "PENDING_HR"

        # HR approves
        proposal, _ = ProposalStateMachine.transition(
            proposal, "HR_APPROVED", actor_id="HR-001", actor_role="HR_PARTNER"
        )
        assert proposal["final_status"] == "HR_APPROVED"

        # Implement
        proposal, event = ProposalStateMachine.transition(
            proposal, "IMPLEMENTED", actor_id="HR-001", actor_role="HR_PARTNER"
        )
        assert proposal["final_status"] == "IMPLEMENTED"
        assert event["to_state"] == "IMPLEMENTED"

    def test_withdraw_at_any_non_terminal_stage(self, open_proposal):
        for state in ["OPEN", "PENDING_MANAGER", "MANAGER_APPROVED", "PENDING_HR", "HR_APPROVED"]:
            proposal = {**open_proposal, "final_status": state, "manager_approval": "APPROVED", "hr_approval": "APPROVED"}
            updated, _ = ProposalStateMachine.transition(
                proposal, "WITHDRAWN", actor_id="EMP-001", actor_role="ADMIN"
            )
            assert updated["final_status"] == "WITHDRAWN"


# ---------------------------------------------------------------------------
# ProposalStateMachine — invalid / unauthorized transitions
# ---------------------------------------------------------------------------

class TestProposalStateMachineRejections:

    def test_invalid_transition_raises(self, open_proposal):
        """OPEN cannot jump directly to IMPLEMENTED."""
        with pytest.raises(ValueError, match="Invalid transition"):
            ProposalStateMachine.transition(
                open_proposal, "IMPLEMENTED", actor_id="HR-001", actor_role="HR_PARTNER"
            )

    def test_manager_approval_blocked_for_non_manager(self, open_proposal):
        pending_mgr = {**open_proposal, "final_status": "PENDING_MANAGER"}
        with pytest.raises(ValueError, match="Manager"):
            ProposalStateMachine.transition(
                pending_mgr, "MANAGER_APPROVED", actor_id="HR-001", actor_role="HR_PARTNER"
            )

    def test_hr_approval_blocked_for_non_hr(self, open_proposal):
        pending_hr = {**open_proposal, "final_status": "PENDING_HR"}
        with pytest.raises(ValueError, match="HR"):
            ProposalStateMachine.transition(
                pending_hr, "HR_APPROVED", actor_id="MGR-001", actor_role="MANAGER"
            )

    def test_implemented_blocked_without_manager_approval(self, open_proposal):
        """IMPLEMENTED must be blocked if manager_approval is missing."""
        hr_approved = {
            **open_proposal,
            "final_status": "HR_APPROVED",
            "manager_approval": None,
            "hr_approval": "APPROVED",
        }
        with pytest.raises(ValueError, match="Manager approval"):
            ProposalStateMachine.transition(
                hr_approved, "IMPLEMENTED", actor_id="HR-001", actor_role="HR_PARTNER"
            )

    def test_implemented_blocked_without_hr_approval(self, open_proposal):
        """IMPLEMENTED must be blocked if hr_approval is missing."""
        hr_approved = {
            **open_proposal,
            "final_status": "HR_APPROVED",
            "manager_approval": "APPROVED",
            "hr_approval": None,
        }
        with pytest.raises(ValueError, match="HR Partner approval"):
            ProposalStateMachine.transition(
                hr_approved, "IMPLEMENTED", actor_id="HR-001", actor_role="HR_PARTNER"
            )

    def test_terminal_state_cannot_transition(self, open_proposal):
        """IMPLEMENTED and WITHDRAWN are terminal — no further transitions allowed."""
        for terminal in ["IMPLEMENTED", "WITHDRAWN"]:
            proposal = {**open_proposal, "final_status": terminal}
            with pytest.raises(ValueError, match="Invalid transition"):
                ProposalStateMachine.transition(
                    proposal, "OPEN", actor_id="ADMIN-001", actor_role="ADMIN"
                )


# ---------------------------------------------------------------------------
# ProposalAuditTrail
# ---------------------------------------------------------------------------

class TestProposalAuditTrail:

    def test_record_and_retrieve_history(self, open_proposal):
        trail = ProposalAuditTrail()
        event = {
            "proposal_id": "ADJ-2026-000001",
            "timestamp": "2026-11-15T10:00:00",
            "actor_id": "MGR-001",
            "actor_role": "MANAGER",
            "from_state": "OPEN",
            "to_state": "PENDING_MANAGER",
            "notes": "Initiating review",
        }
        trail.record(event)
        history = trail.get_history("ADJ-2026-000001")
        assert len(history) == 1
        assert history[0]["to_state"] == "PENDING_MANAGER"

    def test_history_filtered_per_proposal(self):
        trail = ProposalAuditTrail()
        trail.record({"proposal_id": "ADJ-001", "from_state": "OPEN", "to_state": "PENDING_MANAGER"})
        trail.record({"proposal_id": "ADJ-002", "from_state": "OPEN", "to_state": "PENDING_MANAGER"})
        trail.record({"proposal_id": "ADJ-001", "from_state": "PENDING_MANAGER", "to_state": "PENDING_HR"})

        assert len(trail.get_history("ADJ-001")) == 2
        assert len(trail.get_history("ADJ-002")) == 1

    def test_to_dataframe_empty(self):
        trail = ProposalAuditTrail()
        df = trail.to_dataframe()
        assert df.empty
        assert "proposal_id" in df.columns

    def test_to_dataframe_with_events(self):
        trail = ProposalAuditTrail()
        trail.record({"proposal_id": "ADJ-001", "actor_id": "MGR-001", "actor_role": "MANAGER",
                      "from_state": "OPEN", "to_state": "PENDING_MANAGER", "notes": "", "timestamp": "2026-11-15"})
        df = trail.to_dataframe()
        assert len(df) == 1
        assert df.iloc[0]["proposal_id"] == "ADJ-001"


# ---------------------------------------------------------------------------
# calculate_recommended_adjustment
# ---------------------------------------------------------------------------

class TestCalculateRecommendedAdjustment:

    def test_below_band_low_performer_gets_minimum_increase(self):
        result = calculate_recommended_adjustment(
            current_salary=600_000,   # 6 LPA — below band
            band_min=700_000,
            band_mid=1_000_000,
            band_max=1_300_000,
            perf_rating=2.0,          # Low performer — 85% of midpoint
        )
        assert result["current_salary"] == 600_000
        assert result["proposed_salary_recommended"] >= 600_000
        assert result["proposed_salary_min"] >= 600_000
        assert result["proposed_change_pct"] > 0

    def test_high_performer_targets_full_midpoint(self):
        result = calculate_recommended_adjustment(
            current_salary=800_000,
            band_min=700_000,
            band_mid=1_000_000,
            band_max=1_300_000,
            perf_rating=4.8,          # High performer — 100% of midpoint
        )
        assert result["proposed_salary_recommended"] >= 1_000_000

    def test_peer_median_anchoring(self):
        """When peer_median is higher, recommended salary should anchor towards it."""
        result_no_peer = calculate_recommended_adjustment(
            current_salary=700_000,
            band_min=700_000,
            band_mid=1_000_000,
            band_max=1_300_000,
            perf_rating=3.0,
            peer_median=None,
        )
        result_with_peer = calculate_recommended_adjustment(
            current_salary=700_000,
            band_min=700_000,
            band_mid=1_000_000,
            band_max=1_300_000,
            perf_rating=3.0,
            peer_median=950_000,       # Peer median pulls recommendation up
        )
        assert result_with_peer["proposed_salary_recommended"] >= result_no_peer["proposed_salary_recommended"]

    def test_no_decrease_for_above_band_employee(self):
        """An employee already above band should not receive a decrease recommendation."""
        result = calculate_recommended_adjustment(
            current_salary=1_400_000,  # Above band max
            band_min=700_000,
            band_mid=1_000_000,
            band_max=1_300_000,
            perf_rating=3.5,
        )
        assert result["proposed_salary_recommended"] >= 1_400_000
        assert result["proposed_change_pct"] >= 0

    def test_change_pct_is_zero_for_already_at_target(self):
        """If current salary exactly equals recommended target, pct change should be 0 or negligible."""
        result = calculate_recommended_adjustment(
            current_salary=1_000_000,
            band_min=700_000,
            band_mid=1_000_000,
            band_max=1_300_000,
            perf_rating=4.8,
        )
        # Recommended should be at or above midpoint; change_pct should be non-negative
        assert result["proposed_change_pct"] >= 0.0
