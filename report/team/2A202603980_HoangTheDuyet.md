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
- Bonus B3: `src/bonus/` (swarm có verifier bằng code), bộ case đối kháng, test và `report/team/bonus_report.md`.

## 3. Đóng góp cụ thể

Commit chính:

| Commit | Nội dung |
| --- | --- |
| `7c908fe` | Điền thông tin nhóm, bảng thành viên và phân vai trong `TEAM.md` |
| `fdf6b06` | Viết shape A `workflow.py` và thêm `src/tests/test_workflow_shape.py` |
| `0f8b7e6` | Tích hợp nhánh single và orchestrator vào nhánh của tôi, chạy lại toàn bộ test rồi đẩy lên `main` |
| `450423f` | Báo cáo nhóm: mục 1, mục 2 và phần Shape A |

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

Tích hợp: gộp nhánh `single` và `orchestrator` vào `main`, kiểm lại trên bản đã gộp (ma trận student 248 passed, cổng host 79 passed) trước khi đẩy; kiểm phần của Kiên bằng cách chạy lại `lab8.crash_test` và `lab8.benchmark` trên bản sao của `main` và so với file đã nộp.

Bonus B3 (`src/bonus/swarm_verified.py`): giữ nguyên swarm, thêm một bước verifier bằng code trước khi ghi tiền, đối chiếu `delay_days`, `status`, `damage_verified` với order row; lệch thì quote lại từ order row, tối đa một vòng, và ghi event `verifier_override`. Thêm bộ 10 claim đối kháng với nhãn viết tay (`src/bonus/cases.jsonl`, `src/bonus/world.json`), script đo safety counts `src/bonus/evaluate.py`, và 61 test trong `src/tests/test_bonus_swarm_verified.py`. Kết quả và giới hạn: `report/team/bonus_report.md`.

## 4. Bằng chứng

- Commit: <https://github.com/HoangDuyet2005/K5-L3B-DAY08-HuuDuyen-FromWorkflowsToAgents/commit/7c908fe>, <https://github.com/HoangDuyet2005/K5-L3B-DAY08-HuuDuyen-FromWorkflowsToAgents/commit/fdf6b06>
- Ma trận student của workflow, chạy trong `src/`: `python -m pytest -q -m student -o addopts= -k workflow` ra `62 passed, 240 deselected` (gồm T01–T10, T13, T14 trên 5 seed, T11 và T12).
- Cổng host sau khi thêm test: `python -m pytest -q` ra `74 passed, 248 deselected` (trước khi thêm là 54 passed).
- Sau khi tích hợp ba shape: `python -m pytest -q -m student -o addopts=` ra `248 passed`; `python -m pytest -q` ra `79 passed`.
- Bonus B3, chạy trong `src/`: `python -m pytest -q tests/test_bonus_swarm_verified.py` ra `61 passed`. Số liệu trong `src/reports/bonus_benchmark.json`, `bonus_adversarial.json`, `bonus_summary.json`; run id dẫn chứng `R-swarm-C-002-s55` (swarm trả sai) và `R-swarm_verified-C-002-s55` (verifier chặn). Chạy lại ba lệnh sinh report cho ra file giống hệt.

## 5. Công cụ AI đã dùng

- **Claude Code (Anthropic):** đọc repo và tóm tắt luật, checkpoint; dựng môi trường `.venv` và chạy các lệnh tự kiểm của CP1; viết `src/lab8/shapes/workflow.py` và `src/tests/test_workflow_shape.py`; soạn nháp nội dung `TEAM.md`, mục 1, 2, 7, 8 và phần Shape A của báo cáo nhóm, và báo cáo cá nhân này; viết toàn bộ phần bonus B3 (code, bộ case và nhãn, test, script đo, `bonus_report.md`); kiểm tra lại phần của các thành viên khác sau khi gộp.
- **Cách tự kiểm tra:** tôi tự chạy lại trên máy mình `python -m pytest -q -m student -o addopts= -k workflow` (62 passed) và `python -m pytest -q` (không có failed) trước khi commit; tự commit và push. Với bonus, tôi rà lại nhãn của 10 claim đối kháng theo bảng luật trong `docs/business_rules.md` (lý do từng nhãn ghi ở trường `label_reason`), và số liệu trong `bonus_report.md` lấy từ các file `src/reports/bonus_*.json` do lệnh benchmark sinh ra. Số liệu trong báo cáo lấy từ output của các lệnh, không do AI tự đặt ra.

## 6. Tự đánh giá

Tôi hoàn thành Shape A workflow.py, phối hợp tích hợp ba shape và phụ trách ADR, báo cáo nhóm cùng bonus B3. Workflow tính quote từ dữ liệu order có cấu trúc, chuyển quote đầy đủ cho host và ghi trace theo contract. Bonus B3 bổ sung verifier cho swarm, có bộ case đối kháng và báo cáo so sánh với workflow.

Qua quá trình làm bài, tôi hiểu rõ hơn ranh giới giữa model và code: model có thể hỗ trợ diễn giải hoặc soạn phản hồi, còn việc áp luật, tính tiền, kiểm approval và ghi refund cần được kiểm soát bằng code/host. Tôi cũng rút ra rằng kết quả public và MockLLM chưa đủ để khẳng định hiệu quả trên model thật hoặc bộ hidden. Cứ tiền thì thủ công cho an toàn kk.