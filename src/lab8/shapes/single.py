"""Shape B — one ReAct agent.

The agent (decide) may only pick read tools through `lab8.runtime.run_react`
(max 8 steps). Money is computed by `compute_compensation` from the order row,
never from ticket text. After the loop, this shape (not the model) calls
`durability.issue_refund` with the FULL quote; the host enforces approval,
per-order cap and idempotency.

Trace contract v1: every return path goes through `finish()`, which writes
{"run_id", "events"}. We never trace the raw claim row (parent_secret) or the
raw order row (phone/address); only allowlisted views and scalar decisions.
"""

from __future__ import annotations

from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace

SHAPE = "single"
MAX_STEPS = 8


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


def _make_decide(budget: Budget, seed: int, claim: dict[str, Any], trace: Trace):
    """ReAct policy. Fixed tool order; the model call only 'thinks', it never picks money."""
    state: dict[str, Any] = {"order_view": None, "quote": None}

    def decide(seen: dict[str, Any]) -> dict[str, Any]:
        last_tool = seen.get("last_tool")
        result = seen.get("last_result")
        # Think step: one simulated model call per loop iteration (counted in Budget).
        complete(budget, seed=seed, purpose="react", prompt=f"{claim['claim_id']}|{last_tool or 'start'}")

        if last_tool is None:
            return {"tool": "lookup_order", "args": {"order_id": claim["order_id"], "principal_id": claim["principal_id"]}}

        if last_tool == "lookup_order":
            state["order_view"] = result
            trace.add("tool", {"name": "lookup_order", "visible": bool(result.get("visible")), "reason": result.get("reason")})
            if not result.get("visible"):
                return {"final": {"status": "escalated", "error_reason": result.get("reason")}}
            return {"tool": "compute_compensation", "args": {"order": result["order"]}}

        if last_tool == "compute_compensation":
            state["quote"] = result
            trace.add("tool", {"name": "compute_compensation", "amount_vnd": result["amount_vnd"], "reason": result["reason"], "clause_ids": result["clause_ids"]})
            return {"final": {"status": "quoted"}}

        return {"final": {"status": "failed", "error_reason": f"unexpected_tool:{last_tool}"}}

    return decide, state


def _run(conn, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    run_id = make_run_id(SHAPE, claim_id, seed)
    trace = Trace(run_id)

    def done(status: str, proposal: int, reason: str | None) -> RunResult:
        trace.add("decision", {"status": status, "proposal_amount": int(proposal), "reason": reason})
        return finish(conn, shape=SHAPE, claim_id=claim_id, seed=seed, status=status,
                      proposal_amount=proposal, budget=budget, trace=trace, error_reason=reason)

    # Allowlisted claim view (no parent_secret). Only ids go into the trace, never the ticket.
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim.get("found"):
        return done("failed", 0, "unknown_claim")
    trace.add("claim", {"claim_id": claim_id, "has_order_id": bool(claim.get("order_id"))})

    if not claim.get("order_id"):
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        return done("needs_info", 0, "missing_order_id")

    decide, state = _make_decide(budget, seed, claim, trace)
    loop = run_react(conn, budget, observation={"claim": {"claim_id": claim_id}}, decide=decide,
                     max_steps=MAX_STEPS, worker=True)
    trace.add("react", {"stopped": loop["stopped"]})

    final = loop["final"]
    if final.get("status") == "escalated":
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return done("escalated", 0, final.get("error_reason"))
    if final.get("status") != "quoted" or state["quote"] is None:
        return done("failed", 0, final.get("error_reason") or "no_quote")

    proposal = int(state["quote"]["amount_vnd"])
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")
    if proposal <= 0:
        return done("denied", 0, state["quote"].get("reason"))

    # Host is the only writer. Full quote; do not catch-and-swallow InjectedCrash.
    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if not outcome["ok"]:
        return done("failed" if outcome["conflict"] else "denied", proposal, outcome["reason"])
    return done("resolved", proposal, None)