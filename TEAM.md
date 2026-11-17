# Team

## Thông tin nhóm

- Tên nhóm: HuuDuyen
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-HuuDuyen-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/HoangDuyet2005/K5-L3B-DAY08-HuuDuyen-FromWorkflowsToAgents, nhánh `main`, commit chốt điền ở CP5

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Hoàng Thế Duyệt | 2A202603980 |  | HoangDuyet2005 | Điều phối/tích hợp; Shape A `workflow.py`; ADR và báo cáo nhóm |
|   2 | Nguyễn Minh Triết | 2A202603995 |  | minhtriet061203 | Shape B `single.py` (ReAct, tối đa 8 bước) |
|   3 | Lã Quốc Nghị | 2A202603947 |  | quocnghidev | Shape C `orchestrator.py`, handoff và trace |
|   4 | Trần Trung Kiên | 2A202604014 | | ttkien0710 | Safety, kiểm thử liên shape, crash suite và benchmark |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Trần Trung Kiên | Safety/evaluation | `636b958` — test liên shape và bằng chứng sau tích hợp | `src/tests/test_safety_evaluation.py` — 84 test: approval, crash, trace/stdout, cap theo đơn, ticket ablation |
| Lã Quốc Nghị | Orchestrator/handoff | `90141f7` — Shape C orchestrator | `src/tests/test_handoff_secret.py::test_orchestrator_sanitizes_handoff_and_protects_trace`, `test_orchestrator_passes_full_quote_and_survives_crash` |
| Nguyễn Minh Triết | Single ReAct (Shape B) | 6e60031 Shape B single: ReAct read-only, host-only refund | tests/test_single_shape.py (3 test) |
| Hoàng Thế Duyệt | Workflow/tích hợp; bonus B3 | `fdf6b06` — shape A `workflow.py` và test; `0f8b7e6` — tích hợp ba shape vào `main`; bonus B3 `src/bonus/` | `src/tests/test_workflow_shape.py` — 20 test: claim không tồn tại, store hỏng, trace không chứa ticket/secret, ticket không ghi đè order row, model chỉ soạn chữ; `src/tests/test_bonus_swarm_verified.py` — 61 test cho bonus B3 |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603947_LaQuocNghi

### Phần việc phụ trách

- Shape C (`src/lab8/shapes/orchestrator.py`), lọc `handoff` theo allowlist và bảo vệ `trace` theo `Trace contract v1`.

### Đóng góp cụ thể

- Cài đặt `run_claim` trong `src/lab8/shapes/orchestrator.py` (commit `90141f7`).
- Thêm 2 test trong `src/tests/test_handoff_secret.py`: `test_orchestrator_sanitizes_handoff_and_protects_trace`, `test_orchestrator_passes_full_quote_and_survives_crash`.
- Viết phần giải pháp Shape C trong `report/team/group_report.md` và báo cáo cá nhân `report/team/2A202603947_LaQuocNghi.md`.

### Bằng chứng

- Commit `90141f7` trên nhánh `task/quocnghidev`; `.venv/bin/python -m pytest -q` (`79 passed`) và `.venv/bin/python -m pytest -q -m student -o addopts= -k orchestrator` (`62 passed`).

## 2A202603995_NguyenMinhTriet

### Phần việc phụ trách

- Shape B single ReAct: `src/lab8/shapes/single.py`, test `src/tests/test_single_shape.py`.

### Đóng góp cụ thể

- `run_react` tối đa 8 bước, `worker=True`; agent chỉ chọn tool đọc (`lookup_order` → `compute_compensation`), quote tính từ order row, không từ ticket.
- Sau vòng lặp, shape gọi `durability.issue_refund` với quote đầy đủ, truyền `crash_at`, không nuốt `InjectedCrash`; mọi nhánh trả qua `finish()`.
- Trace chỉ ghi id, cờ, tên tool, quote, clause và quyết định; không ghi ticket, claim row, order row.
- 3 test: C-002 denied ở cả 5 seed; chạy lại C-001 vẫn 1 dòng ledger; trace sạch và ≤ 9 model call.

### Bằng chứng

- Commit `6e60031`.
- Ma trận student shape single: 62 passed; `tests/test_single_shape.py`: 3 passed; cổng host xanh.
- Báo cáo chi tiết: `report/team/2A202603995_NguyenMinhTriet.md`.
## MSSV_HoTen

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-
