"""Bonus B3 — test cho swarm + verifier bằng code (`bonus/swarm_verified.py`)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from bonus.swarm_verified import VERIFIED_FACTS, run_claim, verify_facts
from lab8.config_loader import repo_path
from lab8.db import connect, init_store, load_json, load_jsonl
from lab8.durability import InjectedCrash
from lab8.metrics import trial_pass
from lab8.shapes.swarm_reference import run_claim as swarm_run_claim
from tests.conftest import BY_ID

SEEDS = [11, 22, 33, 44, 55]
BONUS_WORLD = load_json(repo_path("bonus", "world.json"))
BONUS_CLAIMS = load_jsonl(repo_path("bonus", "cases.jsonl"))
BONUS_BY_ID = {row["claim_id"]: row for row in BONUS_CLAIMS}


@pytest.fixture
def bonus_db(tmp_path: Path) -> Path:
    store = tmp_path / "bonus.sqlite"
    init_store(store, BONUS_WORLD, BONUS_CLAIMS).close()
    return store


def _events(result) -> list[dict]:
    return json.loads(Path(result.trace_path).read_text(encoding="utf-8"))["events"]


def _kinds(result) -> list[str]:
    return [event["kind"] for event in _events(result)]


def test_verify_facts_reports_only_the_fields_that_disagree():
    structured = {"delay_days": 2, "status": "delivered", "damage_verified": False, "shipping_fee_vnd": 35000}
    assert verify_facts(dict(structured), structured) == {}
    assert verify_facts({**structured, "delay_days": 5}, structured) == {"delay_days": {"used": 5, "order": 2}}
    # Field ngoài danh sách dữ kiện quyết định tiền không được so.
    assert verify_facts({**structured, "shipping_fee_vnd": 1}, structured) == {}
    assert set(VERIFIED_FACTS) == {"delay_days", "status", "damage_verified"}


def test_verifier_blocks_the_swarm_weakness_on_public_t02(public_db, tmp_path):
    """C-002 seed 55: swarm tin ticket (trễ 5 ngày) và trả tiền; bản có verifier từ chối."""
    swarm_store = tmp_path / "swarm.sqlite"
    init_store(swarm_store, load_json(repo_path("data", "public_world_state.json")), list(BY_ID.values())).close()
    swarm = swarm_run_claim("C-002", seed=55, store_path=str(swarm_store))
    assert swarm.status == "resolved", "điểm yếu tham chiếu của swarm phải lộ ở trial này"

    started_at = time.time()
    verified = run_claim("C-002", seed=55, store_path=str(public_db))
    conn = connect(public_db)
    try:
        passed, reason = trial_pass(verified.as_dict(), BY_ID["C-002"]["expected"], conn, started_at=started_at)
    finally:
        conn.close()
    assert passed, reason
    assert verified.status == "denied"
    assert verified.refund_effects == []

    override = [event["payload"] for event in _events(verified) if event["kind"] == "verifier_override"]
    assert len(override) == 1
    assert override[0]["fields"] == {"delay_days": {"used": 5, "order": 2}}
    assert override[0]["swarm_proposal"] > 0
    assert override[0]["verified_proposal"] == 0
    assert override[0]["rounds"] == 1


@pytest.mark.parametrize("seed", SEEDS)
def test_verifier_stays_silent_when_ticket_agrees_with_order(public_db, seed):
    """C-001: ticket và order row cùng ghi 4 ngày. Không override, kết quả như swarm."""
    result = run_claim("C-001", seed=seed, store_path=str(public_db))
    assert result.status == "resolved"
    assert result.proposal_amount == 35000
    kinds = _kinds(result)
    assert "verifier" in kinds
    assert "verifier_override" not in kinds


@pytest.mark.parametrize("claim_id", sorted(BONUS_BY_ID))
@pytest.mark.parametrize("seed", SEEDS)
def test_adversarial_cases_pass_on_every_seed(bonus_db, claim_id, seed):
    """Bộ đối kháng tự viết: swarm_verified khớp nhãn viết tay ở mọi seed."""
    started_at = time.time()
    result = run_claim(claim_id, seed=seed, store_path=str(bonus_db))
    conn = connect(bonus_db)
    try:
        passed, reason = trial_pass(result.as_dict(), BONUS_BY_ID[claim_id]["expected"], conn, started_at=started_at)
    finally:
        conn.close()
    assert passed, reason


def test_understated_ticket_no_longer_costs_the_customer(bonus_db, tmp_path):
    """C-B02: ticket ghi trễ 1 ngày, order ghi 5. Swarm seed 55 từ chối oan; verifier trả đủ."""
    swarm_store = tmp_path / "swarm.sqlite"
    init_store(swarm_store, BONUS_WORLD, BONUS_CLAIMS).close()
    swarm = swarm_run_claim("C-B02", seed=55, store_path=str(swarm_store))
    assert swarm.status == "denied"

    verified = run_claim("C-B02", seed=55, store_path=str(bonus_db))
    assert verified.status == "resolved"
    assert verified.proposal_amount == 40000
    assert [effect["amount_vnd"] for effect in verified.refund_effects] == [40000]


def test_override_that_does_not_change_the_amount_is_still_recorded(bonus_db):
    """C-B05: ticket nói thiếu ngày trễ, nhưng quyền lợi lớn hơn đến từ hỏng hàng đã verify."""
    result = run_claim("C-B05", seed=55, store_path=str(bonus_db))
    override = [event["payload"] for event in _events(result) if event["kind"] == "verifier_override"]
    assert len(override) == 1
    assert override[0]["swarm_proposal"] == override[0]["verified_proposal"] == 150000
    assert result.status == "resolved"


def test_crash_propagates_and_resume_keeps_one_refund(bonus_db):
    with pytest.raises(InjectedCrash):
        run_claim("C-B09", seed=11, store_path=str(bonus_db), crash_at="after_effect_before_checkpoint")
    result = run_claim("C-B09", seed=11, store_path=str(bonus_db))
    conn = connect(bonus_db)
    try:
        rows = conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-B09'").fetchone()["n"]
    finally:
        conn.close()
    assert result.status == "resolved"
    assert rows == 1
    assert result.committed_audit_count == 1


def test_adversarial_corpus_has_hand_written_labels():
    assert len(BONUS_CLAIMS) >= 8
    for claim in BONUS_CLAIMS:
        expected = claim["expected"]
        assert expected["label_reason"].strip(), claim["claim_id"]
        assert expected["status"] in {"resolved", "denied"}
        assert (expected["refund_count"] == 1) == (expected["status"] == "resolved")
