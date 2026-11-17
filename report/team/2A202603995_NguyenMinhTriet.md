# Báo cáo cá nhân — 2A202603995_NguyenMinhTriet

## 1. Thông tin thành viên

- Họ tên: Nguyễn Minh Triết
- MSSV: 2A202603995
- Email: mtriet674@gmail.com
- GitHub: minhtriet061203

## 2. Phần việc phụ trách

Shape B — single ReAct agent: `src/lab8/shapes/single.py` và test riêng `src/tests/test_single_shape.py`.

## 3. Đóng góp cụ thể

- Commit chính: `<HASH>` — "Shape B single: ReAct read-only, host-only refund, tests".
- Cài `run_claim` cho shape single bằng `lab8.runtime.run_react` (`max_steps=8`, `worker=True`): hàm `decide` chỉ chọn tool đọc theo thứ tự `lookup_order` → `compute_compensation`, rồi trả `final`. Mỗi bước ReAct có một lời gọi MockLLM được cộng vào `Budget` để cost so sánh được với các shape khác.
- Ranh giới code / model: số tiền do `compute_compensation` tính từ order row, không lấy số ngày trễ trong ticket. Model không gọi `issue_refund`; sau vòng lặp, code của shape gọi `durability.issue_refund` với **quote đầy đủ** để host tự kiểm approval, trần theo đơn (T13, T14) và idempotency.
- Xử lý đủ các nhánh theo contract: thiếu `order_id` → `needs_info`; không thấy đơn / sai principal → `escalated`; quote = 0 → `denied` (không gọi host); host từ chối → `denied` với `proposal_amount` = quote; conflict → `failed`; thành công → `resolved`. Mọi nhánh trả qua `common.finish()`.
- Crash: truyền `crash_at` vào `issue_refund`, ghi trace rồi raise lại `InjectedCrash`, không nuốt lỗi.
- Trace chỉ ghi `claim_id`, cờ `has_order_id`, tên tool, `visible`/`reason`, số tiền quote, `clause_ids` và quyết định cuối. Cố ý **không** ghi ticket, claim row (có `parent_secret`), order row (SĐT, địa chỉ, tên hàng, internal note).
- Test thêm (`tests/test_single_shape.py`, 3 test):
  - `test_single_ignores_ticket_delay_on_every_seed`: C-002 ticket ghi "trễ 5 ngày" nhưng DB trễ 2 ngày → `denied` ở cả 5 seed.
  - `test_single_rerun_same_claim_keeps_one_refund`: chạy lại C-001 với seed khác vẫn một dòng ledger 35.000.
  - `test_single_trace_is_clean_and_bounded`: trace đúng contract v1, không chứa secret/PII/ticket, số model call ≤ 8 + 1.

## 4. Bằng chứng

- `python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"` → 62 passed.
- `python -m pytest -q tests/test_single_shape.py` → 3 passed.
- `python -m pytest -q` (cổng host) → 57 passed.
- Ví dụ trace: run id `R-single-C-001-s11` (5 event: claim, 2 tool, react, decision).
- Số liệu benchmark chính thức của shape single: lấy từ `src/reports/benchmark.json` sau khi nhóm chạy (xem `report/team/decision_adr.md`).

## 5. Công cụ AI đã dùng

- Claude: đọc đề và tóm tắt các bước, gợi ý cấu trúc `decide` cho `run_react`, gợi ý test.
- Tự kiểm tra: đọc lại code theo `docs/business_rules.md` và `docs/contracts.md`; chạy ma trận student của shape single (62/62), test riêng (3/3) và cổng host trên máy mình; mở file trace để xác nhận không có field nhạy cảm. Lưu ý phát hiện khi kiểm tra: lệnh `-k single` trong CHECKPOINTS còn khớp tên hàm `test_public_single_run_cases` nên chạy cả test của shape khác; phải lọc thêm `not workflow and not orchestrator and not swarm`.

## 6. Tự đánh giá

Shape single qua đủ 62 test public và 3 test riêng, giữ đúng ranh giới: model chỉ đọc, host là nơi duy nhất ghi tiền. Giới hạn: `decide` hiện đi theo thứ tự tool cố định nên hành vi gần với workflow; MockLLM không phản ánh độ dao động của model thật, nên kết quả pass rate cao trên bộ public chưa chứng minh single bền khi dùng LLM thật.