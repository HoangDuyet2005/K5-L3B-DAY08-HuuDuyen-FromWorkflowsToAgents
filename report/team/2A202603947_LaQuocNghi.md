# Báo cáo cá nhân — 2A202603947_LaQuocNghi

## 1. Thông tin thành viên

- Họ tên: Lã Quốc Nghị
- MSSV: 2A202603947
- Email: quocnghidev@gmail.com
- GitHub: quocnghidev

## 2. Phần việc phụ trách

- Triển khai **Shape C (`orchestrator`)** trong `src/lab8/shapes/orchestrator.py`: điều phối xử lý claim theo mô hình orchestrator kết hợp read-only investigator.
- Bảo đảm ranh giới bảo mật giữa orchestrator và investigator: lọc `handoff` theo allowlist (`lab8.handoff.make_handoff`), không cấp tool ghi cho investigator, và bảo vệ `trace` theo `Trace contract v1`.
- Bổ sung unit test cho Shape C trong `src/tests/test_handoff_secret.py` và viết phần giải pháp Shape C trong `report/team/group_report.md`.

## 3. Đóng góp cụ thể

- **Commit chính:** `90141f7` (`Shape C orchestrator`) trên nhánh `task/quocnghidev`.
- **Test đã thêm trong `src/tests/test_handoff_secret.py`:**
  - `test_orchestrator_sanitizes_handoff_and_protects_trace`
  - `test_orchestrator_passes_full_quote_and_survives_crash`
- **Quyết định kỹ thuật:**
  - Đọc claim qua `get_claim_view(conn, claim_id)` (chỉ lấy `claim_id`, `principal_id`, `order_id`, `ticket`) để không đọc `parent_secret` và `raw_headers_json`.
  - Dựng gói giao việc qua `make_handoff(..., facts={}, allowed_tools=["lookup_order", "lookup_policy", "lookup_refund_history", "compute_compensation"])` và chạy `run_readonly_investigators`; từ chối ngay ở code nếu `order_view` không `visible` (`escalated`).
  - Tính quote từ dữ liệu đơn có cấu trúc (`order_view["order"]`), bỏ qua số ngày trễ tự khai trong ticket; `MockLLM` (`complete`) chỉ dùng cho `plan` và `draft`.
  - Khi `proposal > 0`, luôn truyền **quote đầy đủ** vào `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)` để host kiểm approval, idempotency và trần hoàn tiền theo đơn; bắt `InjectedCrash` chỉ để ghi `trace.write()` rồi re-raise.
  - Chỉ ghi các event đã sanitize vào trace (`handoff`, `investigator`, `quote`, `decision`/`error`/`crash`); loại bỏ hoàn toàn `parent_secret`, `raw_headers`, SĐT, địa chỉ, tên hàng và ghi chú nội bộ.

## 4. Bằng chứng

- Nhánh làm việc: `task/quocnghidev` · Commit code & test: `90141f7`.
- Các file đóng góp:
  - `src/lab8/shapes/orchestrator.py`
  - `src/tests/test_handoff_secret.py`
  - `report/team/group_report.md`
- Kết quả kiểm thử (chạy tại `src/`):
  - `.venv/bin/python -m lab8.smoke` → `lab8.smoke pass`
  - `.venv/bin/python -m pytest -q` → `79 passed, 248 deselected` (gồm 2 test mới thêm)
  - `.venv/bin/python -m pytest -q -m student -o addopts= -k orchestrator` → `62 passed, 265 deselected`

## 5. Công cụ AI đã dùng

- **Công cụ:** Trợ lý lập trình AI trong IDE (Antigravity).
- **Mục đích:** Phân tích yêu cầu lab, hỗ trợ triển khai `run_claim` cho Shape C (`orchestrator.py`), thiết kế các test kiểm tra allowlist handoff, chặn rò rỉ secret/PII và xử lý crash (`test_handoff_secret.py`), cũng như biên tập ghi chú kỹ thuật cho `group_report.md`.
- **Tự kiểm tra kết quả:** Đối chiếu từng nhánh xử lý với `docs/business_rules.md`, `docs/contracts.md`, `src/lab8/handoff.py`; chạy trực tiếp `lab8.smoke`, `pytest -q`, và `pytest -q -m student -o addopts= -k orchestrator` sau khi sửa code để xác minh toàn bộ test pass và trace sạch.

## 6. Tự đánh giá

- Hoàn thành đầy đủ Shape C (`orchestrator`), vượt qua 62/62 test student của shape và cổng host `pytest -q`, bảo đảm đúng ranh giới code/model, handoff allowlist, trace contract v1 và cơ chế crash/idempotency.
- Sẵn sàng merge vào nhánh `main` để nhóm chạy crash suite và benchmark tổng hợp ở CP5.
