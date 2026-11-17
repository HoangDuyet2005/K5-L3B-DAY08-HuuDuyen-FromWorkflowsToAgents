"""Test riêng cho shape A (workflow): các ca mà ma trận public T01–T14 chưa kiểm."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.metrics import check_trace
from lab8.shapes.workflow import run_claim
from tests.conftest import BY_ID

SEEDS = [11, 22, 33, 44, 55]
SINGLE_RUN_CLAIMS = [f"C-{i:03d}" for i in range(1, 11)] + ["C-013", "C-014"]


def _ledger_rows(store: Path) -> int:
    conn = connect(store)
    try:
        return int(conn.execute("SELECT COUNT(*) AS n FROM refund_ledger").fetchone()["n"])
    finally:
        conn.close()


def test_unknown_claim_fails_closed(public_db):
    """Claim không tồn tại: `failed`, không đề xuất tiền, không ghi thêm dòng ledger."""
    before = _ledger_rows(public_db)
    started_at = time.time()
    result = run_claim("C-KHONG-CO", seed=11, store_path=str(public_db))

    assert result.status == "failed"
    assert result.error_reason == "unknown_claim"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert _ledger_rows(public_db) == before
    assert check_trace(result.as_dict(), started_at=started_at) == (True, "ok")


def test_broken_store_returns_failed_instead_of_raising(tmp_path):
    """Store không có bảng nào: run_claim vẫn trả RunResult có trace, không ném exception."""
    store = tmp_path / "empty.sqlite"
    started_at = time.time()
    result = run_claim("C-001", seed=11, store_path=str(store))

    assert result.status == "failed"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert check_trace(result.as_dict(), started_at=started_at) == (True, "ok")


@pytest.mark.parametrize("claim_id", SINGLE_RUN_CLAIMS)
def test_trace_never_contains_ticket_or_secret(public_db, claim_id):
    """Trace chỉ ghi view đã qua allowlist: không có chữ của ticket, secret hay header."""
    result = run_claim(claim_id, seed=11, store_path=str(public_db))
    claim = BY_ID[claim_id]
    blob = Path(result.trace_path).read_text(encoding="utf-8")
    blob += json.dumps(result.as_dict(), ensure_ascii=False)

    assert claim["ticket"] not in blob
    assert claim["parent_secret"] not in blob
    assert "CANARY_SECRET_" not in blob
    assert "Authorization" not in blob


@pytest.mark.parametrize("seed", SEEDS)
def test_ticket_delay_does_not_override_order_row(public_db, seed):
    """C-002: ticket ghi trễ 5 ngày, order ghi 2 ngày. Mọi seed đều từ chối, không gọi host."""
    result = run_claim("C-002", seed=seed, store_path=str(public_db))

    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.committed_audit_count == 0


def test_model_only_drafts_the_reply(public_db):
    """Workflow chỉ gọi model một lần (soạn câu trả lời); số tiền đến từ tool của code."""
    result = run_claim("C-001", seed=11, store_path=str(public_db))

    assert result.status == "resolved"
    assert result.proposal_amount == 35000
    assert result.model_calls == 1
    assert result.tool_calls == 3
