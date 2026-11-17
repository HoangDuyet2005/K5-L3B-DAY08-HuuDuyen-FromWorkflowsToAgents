"""Bonus B3 — swarm + verifier bằng code trước khi ghi tiền.

Chữ ký giống bốn shape chính:

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Chạy cạnh bốn shape bằng cờ của benchmark, không sửa `lab8/shapes/__init__.py`:

    python -m lab8.benchmark --shapes workflow,swarm,swarm_verified \
        --extra-shape swarm_verified=bonus.swarm_verified:run_claim \
        --seeds 11,22,33,44,55 --out reports/bonus_benchmark.json

Ý tưởng. Phần swarm được giữ nguyên hành vi của `lab8/shapes/swarm_reference.py`:
cùng các lần gọi model (peer, parse, draft), cùng investigator đọc, và cùng điểm yếu
tham chiếu (seed chia hết cho 5 thì tin số ngày trễ ghi trong ticket). Thứ duy nhất
được thêm là một bước **verifier bằng code** nằm giữa "swarm đề xuất" và "host ghi":

1. So các dữ kiện swarm đã dùng để quote (`delay_days`, `status`, `damage_verified`)
   với order row có cấu trúc do tool `lookup_order` trả về.
2. Nếu lệch: quote lại từ dữ liệu có cấu trúc, đúng một vòng sửa, và ghi event
   `verifier_override` vào trace.
3. Nếu khớp: giữ nguyên đề xuất của swarm, ghi event `verifier` với `ok=True`.

Verifier không gọi model và không đọc ticket. Sau bước này số tiền luôn đến từ
`compute_compensation` trên order row, nên host nhận cùng một quote ở mọi seed.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete, parse_delay_days
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import compute_compensation, get_claim_view, tool_cost
from lab8.trace import Trace

SHAPE = "swarm_verified"
# Các dữ kiện quyết định số tiền. Verifier chỉ so đúng ba field này.
VERIFIED_FACTS = ("delay_days", "status", "damage_verified")
MAX_CORRECTION_ROUNDS = 1


def verify_facts(used: dict[str, Any], structured: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Trả về các dữ kiện swarm đã dùng mà lệch với order row.

    Kết quả rỗng nghĩa là khớp. Mỗi phần tử có dạng
    {"used": <giá trị swarm dùng>, "order": <giá trị trong order row>}.
    """
    mismatch: dict[str, dict[str, Any]] = {}
    for key in VERIFIED_FACTS:
        if used.get(key) != structured.get(key):
            mismatch[key] = {"used": used.get(key), "order": structured.get(key)}
    return mismatch


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def done(status: str, proposal: int, reason: str | None) -> RunResult:
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

    # ---- Phần swarm: giữ nguyên hành vi của swarm_reference ----
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim["found"]:
        trace.add("error", {"reason": "unknown_claim"})
        return done("failed", 0, "unknown_claim")

    ticket = claim["ticket"]
    complete(budget, seed=seed, purpose="peer", prompt=ticket)
    parsed_delay = parse_delay_days(ticket)
    complete(budget, seed=seed, purpose="parse", prompt=ticket)

    if not claim["order_id"]:
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return done("needs_info", 0, "missing_order_id")

    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_applicable_policy",
        facts={},
        allowed_tools=["lookup_order", "lookup_policy", "compute_compensation"],
    )
    trace.add("handoff", safe_dump(handoff))
    investigated = run_readonly_investigators(conn, budget, handoff, principal_id=claim["principal_id"])
    tools_out = investigated["tools"]
    order_view = tools_out.get("lookup_order", {})
    trace.add(
        "investigator",
        {
            "lookup_order": order_view,
            "policy_count": len((tools_out.get("lookup_policy") or {}).get("policies") or []),
        },
    )
    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return done("escalated", 0, order_view.get("reason"))

    structured = dict(order_view["order"])  # nguồn sự thật: order row qua allowlist
    used = dict(structured)  # dữ kiện swarm sẽ dùng để quote
    # Điểm yếu tham chiếu của swarm, giữ nguyên để đo: seed % 5 == 0 thì tin ticket.
    if parsed_delay is not None and parsed_delay != int(structured["delay_days"]) and seed % 5 == 0:
        used["delay_days"] = parsed_delay
        trace.add("model_override", {"delay_days": parsed_delay})

    quote = tools_out["compute_compensation"]
    if used["delay_days"] != structured["delay_days"]:
        budget.add_tool(tool_cost())
        quote = compute_compensation(conn, used)
    swarm_proposal = int(quote["amount_vnd"])

    # ---- Verifier bằng code: thứ duy nhất được thêm so với swarm ----
    mismatch = verify_facts(used, structured)
    rounds = 0
    if mismatch and rounds < MAX_CORRECTION_ROUNDS:
        rounds += 1
        budget.add_tool(tool_cost())
        quote = compute_compensation(conn, structured)
        trace.add(
            "verifier_override",
            {
                "fields": mismatch,
                "swarm_proposal": swarm_proposal,
                "verified_proposal": int(quote["amount_vnd"]),
                "rounds": rounds,
            },
        )
    else:
        trace.add("verifier", {"ok": True, "checked": list(VERIFIED_FACTS)})

    proposal = int(quote["amount_vnd"])
    trace.add("quote", quote)
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        return done("denied", 0, quote.get("reason"))

    # Host vẫn là người ghi duy nhất. Truyền quote đầy đủ và crash_at.
    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if not outcome["ok"]:
        return done("failed" if outcome["conflict"] else "denied", proposal, outcome["reason"])
    return done("resolved", proposal, None)
