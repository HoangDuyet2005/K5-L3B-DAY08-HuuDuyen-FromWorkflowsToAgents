"""Tests riêng cho Shape B (single ReAct) — minhtriet061203."""

from __future__ import annotations

import json

from lab8.db import connect
from lab8.durability import get_refund
from lab8.shapes.single import MAX_STEPS, run_claim

SEEDS = [11, 22, 33, 44, 55]


def test_single_ignores_ticket_delay_on_every_seed(public_db):
    # C-002: ticket nói "trễ 5 ngày" nhưng order row trễ 2 ngày -> phải denied ở mọi seed.
    for seed in SEEDS:
        result = run_claim("C-002", seed=seed, store_path=str(public_db))
        assert result.status == "denied", seed
        assert result.proposal_amount == 0
        assert result.refund_effects == []


def test_single_rerun_same_claim_keeps_one_refund(public_db):
    first = run_claim("C-001", seed=11, store_path=str(public_db))
    second = run_claim("C-001", seed=22, store_path=str(public_db))
    assert first.status == second.status == "resolved"
    assert first.proposal_amount == second.proposal_amount == 35000
    conn = connect(public_db)
    try:
        assert int(get_refund(conn, "C-001")["amount_vnd"]) == 35000
        assert conn.execute("SELECT COUNT(*) FROM refund_ledger WHERE claim_id = 'C-001'").fetchone()[0] == 1
    finally:
        conn.close()


def test_single_trace_is_clean_and_bounded(public_db):
    result = run_claim("C-001", seed=11, store_path=str(public_db))
    with open(result.trace_path, encoding="utf-8") as fh:
        raw = fh.read()
    trace = json.loads(raw)
    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list)
    for banned in ("CANARY_SECRET", "parent_secret", "phone", "address", "internal_note", "ticket"):
        assert banned not in raw
    assert result.model_calls <= MAX_STEPS + 1  # tối đa 8 bước ReAct + 1 lần soạn trả lời