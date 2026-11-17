# Báo cáo cá nhân — 2A202603980_HoangTheDuyet

## 1. Thông tin thành viên

- Họ tên: Hoàng Thế Duyệt
- MSSV: 2A202603980
- Email:
- GitHub: HoangDuyet2005

## 2. Phần việc phụ trách

- Shape A: `src/lab8/shapes/workflow.py` (workflow cố định).
- Điều phối và tích hợp: tạo repo nhóm, điền `TEAM.md`, gộp nhánh của các thành viên vào `main` và giữ cổng host xanh.
- `report/team/decision_adr.md` và ghép `report/team/group_report.md` từ phần của các thành viên.

## 3. Đóng góp cụ thể

Commit chính:

| Commit | Nội dung |
| --- | --- |
| `7c908fe` | Điền thông tin nhóm, bảng thành viên và phân vai trong `TEAM.md` |
| `fdf6b06` | Viết shape A `workflow.py` và thêm `src/tests/test_workflow_shape.py` |

Test đã thêm: `src/tests/test_workflow_shape.py` (20 test, chạy trong cổng host):

- `test_unknown_claim_fails_closed`
- `test_broken_store_returns_failed_instead_of_raising`
- `test_trace_never_contains_ticket_or_secret` (12 claim public)
- `test_ticket_delay_does_not_override_order_row` (5 seed)
- `test_model_only_drafts_the_reply`

Quyết định kỹ thuật trong `workflow.py`:

- Thứ tự bước cố định trong code: `get_claim_view` → kiểm `order_id` → `lookup_order` theo principal của claim → `compute_compensation` → `durability.issue_refund`.
- Số tiền lấy từ `compute_compensation` trên order row. Shape không đọc số ngày trễ trong ticket.
- Quote bằng 0 thì trả `denied` và không gọi host. Quote dương thì luôn gọi `issue_refund` với **quote đầy đủ**, để host tự kiểm approval, tự trừ phần đơn đã hoàn và tự ghi audit `policy_denied`.
- Truyền `crash_at` vào `issue_refund` và để `InjectedCrash` đi ra ngoài. Lỗi khác được bắt lại và trả `failed` kèm trace, chỉ ghi tên loại lỗi.
- MockLLM chỉ gọi một lần để soạn câu trả lời; prompt chỉ có status và số tiền.
- Trace chỉ ghi view đã qua allowlist (`lookup_order`, quote, kết quả của host). Cố ý không ghi ticket, claim row và order row thô.

Phần tích hợp, ADR và báo cáo nhóm sẽ bổ sung vào mục này khi có commit tương ứng.

## 4. Bằng chứng

- Commit: <https://github.com/HoangDuyet2005/K5-L3B-DAY08-HuuDuyen-FromWorkflowsToAgents/commit/7c908fe>, <https://github.com/HoangDuyet2005/K5-L3B-DAY08-HuuDuyen-FromWorkflowsToAgents/commit/fdf6b06>
- Ma trận student của workflow, chạy trong `src/`: `python -m pytest -q -m student -o addopts= -k workflow` ra `62 passed, 240 deselected` (gồm T01–T10, T13, T14 trên 5 seed, T11 và T12).
- Cổng host sau khi thêm test: `python -m pytest -q` ra `74 passed, 248 deselected` (trước khi thêm là 54 passed).
- Run id, số liệu benchmark và crash suite: bổ sung sau khi nhóm sinh `src/reports/benchmark.json` và `src/reports/crash.json`.

## 5. Công cụ AI đã dùng

- **Claude Code (Anthropic):** đọc repo và tóm tắt luật, checkpoint; dựng môi trường `.venv` và chạy các lệnh tự kiểm của CP1; viết `src/lab8/shapes/workflow.py` và `src/tests/test_workflow_shape.py`; soạn nháp nội dung `TEAM.md` và báo cáo cá nhân này.
- **Cách tự kiểm tra:** tôi tự chạy lại trên máy mình `python -m pytest -q -m student -o addopts= -k workflow` (62 passed) và `python -m pytest -q` (không có failed) trước khi commit; tự commit và push. Số liệu trong báo cáo lấy từ output của các lệnh này, không do AI tự đặt ra.

## 6. Tự đánh giá

...
