"""Shape A — deterministic workflow. Student work.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Suggested steps. Money stays in code (`lab8.tools.compute_compensation`).

1. Open the store. Read the claim through `get_claim_view` (not SELECT *).
2. Missing order_id -> status `needs_info`. Do not write the ledger.
3. `lookup_order`. If not visible -> `escalated`. Do not copy phone, address, item, internal note.
4. Quote from the order row. Ignore delay numbers written in the ticket.
5. Quote amount 0 -> `denied`. Do not call issue_refund.
6. Quote amount > 0 -> `durability.issue_refund(conn, claim_id, <full quote>)`.
   Pass the FULL quote. The host checks the claim's own approval and subtracts
   what earlier claims already got for the same order (T13, T14). Do not
   subtract it yourself or the host subtracts twice.
   Auth failure or order already refunded -> `denied` (the host writes `policy_denied`).
   `proposal_amount` stays the full quote. Amount conflict -> `failed`.
7. Success -> `resolved`. One ledger row, one `refund_committed` audit.
8. Use MockLLM only to draft the reply text, if you want a model call at all.

The model must not choose the refund amount and must not commit the refund.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.

Ranh giới code / model của shape này:

- Code quyết: thứ tự bước, đọc order theo principal, số tiền (`compute_compensation`),
  và việc gọi `durability.issue_refund`.
- Model (MockLLM) chỉ soạn câu trả lời ở bước cuối. Prompt chỉ chứa status và số tiền,
  không chứa ticket, nên chữ trong ticket không thể đổi kết quả.
- Trace chỉ ghi view đã qua allowlist (`lookup_order`, quote, kết quả của host).
  Không ghi ticket, claim row hay order row thô.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace

SHAPE = "workflow"


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at, budget=budget, trace=trace)
    except InjectedCrash:
        # Crash mô phỏng phải đi ra ngoài (T12). Không nuốt.
        raise
    except Exception as exc:  # run_claim không được ném lỗi khác ra grader.
        return _failed(conn, claim_id, seed, budget, trace, type(exc).__name__)
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
    budget: Budget,
    trace: Trace,
) -> RunResult:
    def done(status: str, proposal: int, reason: str | None) -> RunResult:
        # Bước 8: model chỉ soạn chữ. Prompt không chứa ticket.
        complete(budget, seed=seed, purpose="draft", prompt=f"status={status} proposal={proposal}")
        trace.add("decision", {"status": status, "proposal_amount": proposal, "reason": reason})
        return finish(
            conn,
            shape=SHAPE,
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )

    # Bước 1: đọc claim qua view allowlist (không có parent_secret, header).
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim["found"]:
        trace.add("claim", {"found": False})
        return done("failed", 0, "unknown_claim")
    order_id = claim["order_id"]
    trace.add("claim", {"found": True, "has_order_id": bool(order_id)})

    # Bước 2: thiếu mã đơn thì hỏi lại. Không đoán mã đơn từ chữ trong ticket.
    if not order_id:
        return done("needs_info", 0, "missing_order_id")

    # Bước 3: đọc order theo principal của claim.
    budget.add_tool(tool_cost())
    order_view = lookup_order(conn, order_id, claim["principal_id"])
    trace.add("lookup_order", order_view)
    if not order_view["visible"]:
        return done("escalated", 0, order_view["reason"])

    # Bước 4: tiền do code tính từ order row và policy hiện hành.
    budget.add_tool(tool_cost())
    quote = compute_compensation(conn, order_view["order"])
    proposal = int(quote["amount_vnd"])
    trace.add("quote", quote)

    # Bước 5: không có quyền lợi thì từ chối, không gọi host.
    if proposal <= 0:
        return done("denied", 0, quote["reason"])

    # Bước 6: truyền quote đầy đủ. Host kiểm approval, trần theo đơn, idempotency.
    outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    trace.add("issue_refund", {"ok": outcome["ok"], "reason": outcome["reason"], "conflict": outcome["conflict"]})
    if not outcome["ok"]:
        return done("failed" if outcome["conflict"] else "denied", proposal, outcome["reason"])

    # Bước 7.
    return done("resolved", proposal, None)


def _failed(
    conn: sqlite3.Connection,
    claim_id: str,
    seed: int,
    budget: Budget,
    trace: Trace,
    reason: str,
) -> RunResult:
    """Lỗi ngoài dự kiến: trả `failed` có trace, chỉ ghi tên loại lỗi (không ghi message)."""
    trace.add("error", {"reason": reason})
    try:
        return finish(
            conn,
            shape=SHAPE,
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )
    except Exception:
        # Không đọc được ledger (ví dụ store hỏng): vẫn trả RunResult đúng contract.
        return RunResult(
            run_id=trace.run_id,
            claim_id=claim_id,
            shape=SHAPE,
            seed=seed,
            status="failed",
            proposal_amount=0,
            refund_effects=[],
            committed_audit_count=0,
            model_calls=budget.model_calls,
            tool_calls=budget.tool_calls,
            input_tokens=budget.input_tokens,
            output_tokens=budget.output_tokens,
            cost_estimate=round(budget.cost_estimate, 6),
            trace_path=trace.write(),
            error_reason=reason,
        )
