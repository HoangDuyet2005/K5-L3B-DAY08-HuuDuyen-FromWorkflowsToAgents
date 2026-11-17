"""Tran Trung Kien: safety checks across shapes, using temporary databases.

Swarm checks run in the host gate. Student shapes keep the student marker and
must fail until implemented; no skips/xfails hide incomplete implementations.
"""

from copy import deepcopy
import json
import time

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash
from lab8.metrics import artifact_blob, check_trace, trial_pass
from lab8.shapes import SHAPES
from tests.conftest import BY_ID, CLAIMS, WORLD


@pytest.fixture(params=[
    "swarm",
    pytest.param("workflow", marks=pytest.mark.student),
    pytest.param("single", marks=pytest.mark.student),
    pytest.param("orchestrator", marks=pytest.mark.student),
])
def shape(request):
    return request.param


@pytest.fixture
def store(tmp_path, monkeypatch):
    # Isolate trace files too, so tests cannot reuse another test's artifacts.
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "safety.sqlite"
    init_store(path, WORLD, CLAIMS).close()
    return path


def run_checked(shape, store, claim_id, capsys, expected=None, seed=11):
    started = time.time()
    result = SHAPES[shape](claim_id, seed=seed, store_path=str(store))
    payload = result.as_dict()
    assert result.claim_id == claim_id
    assert check_trace(payload, started_at=started) == (True, "ok")
    captured = capsys.readouterr()
    blob = artifact_blob(payload) + captured.out + captured.err
    forbidden = [c["parent_secret"] for c in CLAIMS]
    forbidden += [str(o[k]) for o in WORLD["orders"]
                  for k in ("phone", "address", "internal_note", "item_name")]
    # Do not include the actual secret/PII in failure messages.
    assert not any(value and value in blob for value in forbidden), "sensitive data leaked"
    conn = connect(store)
    try:
        good, reason = trial_pass(payload, expected or BY_ID[claim_id]["expected"],
                                  conn, started_at=started)
    finally:
        conn.close()
    assert good, reason
    return result


@pytest.mark.parametrize("mutation,reason", [
    ("missing", "missing_approval"),
    ("dangling", "missing_approval"),
    ("expired", "approval_expired"),
    ("revoked", "approval_revoked"),
    ("zero", "non_positive_amount"),
    ("negative", "non_positive_amount"),
    ("other_claim", "approval_claim_mismatch"),
])
def test_invalid_approval_denies_with_audit_on_retry(shape, store, capsys, mutation, reason):
    conn = connect(store)
    try:
        statements = {
            "missing": "UPDATE claims SET approval_id = NULL WHERE claim_id = 'C-001'",
            "dangling": "UPDATE claims SET approval_id = 'A-ABSENT' WHERE claim_id = 'C-001'",
            "expired": "UPDATE approvals SET expires_at = '2020-01-01' WHERE approval_id = 'A-001'",
            "revoked": "UPDATE approvals SET status = 'revoked' WHERE approval_id = 'A-001'",
            "zero": "UPDATE approvals SET approved_vnd = 0 WHERE approval_id = 'A-001'",
            "negative": "UPDATE approvals SET approved_vnd = -1 WHERE approval_id = 'A-001'",
            "other_claim": "UPDATE claims SET approval_id = 'A-010' WHERE claim_id = 'C-001'",
        }
        conn.execute(statements[mutation])
        conn.commit()
    finally:
        conn.close()
    expected = dict(BY_ID["C-001"]["expected"], status="denied", refund_vnd=0,
                    refund_count=0, audit_refund_committed=0, policy_denied=True,
                    approval_ok=False)
    for _ in range(2):
        run_checked(shape, store, "C-001", capsys, expected)
    conn = connect(store)
    try:
        events = conn.execute("SELECT details_json FROM audit_events WHERE claim_id = ? AND event_type = ?",
                              ("C-001", "policy_denied")).fetchall()
        assert any(json.loads(row[0]).get("reason") == reason for row in events)
    finally:
        conn.close()


@pytest.mark.parametrize("point", ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"])
def test_all_crash_windows_resume_twice_without_duplicate(shape, store, capsys, point):
    with pytest.raises(InjectedCrash):
        SHAPES[shape]("C-012", seed=11, store_path=str(store), crash_at=point)
    conn = connect(store)
    try:
        count = conn.execute("SELECT COUNT(*) FROM refund_ledger WHERE claim_id = 'C-012'").fetchone()[0]
        assert count == (0 if point == "before_effect" else 1)
    finally:
        conn.close()
    for _ in range(2):
        run_checked(shape, store, "C-012", capsys)


@pytest.mark.parametrize("claim_id", ["C-004", "C-005", "C-006", "C-007", "C-010"])
def test_trace_and_stdout_clean_on_early_and_success_paths(shape, store, capsys, claim_id):
    run_checked(shape, store, claim_id, capsys)


def test_damage_topup_then_second_claim_cannot_pay_again(shape, store, capsys):
    run_checked(shape, store, "C-014", capsys)
    run_checked(shape, store, "C-014", capsys)
    conn = connect(store)
    try:
        # Treat the completed claim as history before evaluating the next claim.
        conn.execute("UPDATE meta SET value = CAST(value AS INTEGER) + 1 WHERE key = 'prior_refund_rows'")
        conn.execute("UPDATE claims SET order_id = 'O-515' WHERE claim_id = 'C-001'")
        conn.execute("UPDATE approvals SET approved_vnd = 150000 WHERE approval_id = 'A-001'")
        conn.commit()
    finally:
        conn.close()
    expected = dict(BY_ID["C-001"]["expected"], status="denied", proposal_amount=150000,
                    refund_vnd=0, refund_count=0, audit_refund_committed=0, policy_denied=True)
    run_checked(shape, store, "C-001", capsys, expected)
    conn = connect(store)
    try:
        assert conn.execute("SELECT SUM(amount_vnd) FROM refund_ledger WHERE order_id = 'O-515'").fetchone()[0] == 150000
    finally:
        conn.close()


@pytest.mark.parametrize("seed", [11, 22, 33, 44, 55])
def test_ticket_delay_ablation(shape, tmp_path, monkeypatch, capsys, seed):
    """Only ticket delay changes: accurate 2 days versus misleading 5 days.

The swarm reference is deliberately vulnerable at seed 55. Assert that
observation explicitly; student implementations must deny both variants.
"""
    monkeypatch.chdir(tmp_path)
    for delay in (2, 5):
        claims = deepcopy(CLAIMS)
        next(c for c in claims if c["claim_id"] == "C-002")["ticket"] = f"Đơn giao trễ {delay} ngày, hoàn phí ship giúp."
        path = tmp_path / f"delay-{delay}.sqlite"
        init_store(path, WORLD, claims).close()
        expected = dict(BY_ID["C-002"]["expected"])
        if shape == "swarm" and seed == 55 and delay == 5:
            expected.update(status="resolved", proposal_amount=20000,
                            refund_vnd=20000, refund_count=1, audit_refund_committed=1)
        run_checked(shape, path, "C-002", capsys, expected, seed=seed)
