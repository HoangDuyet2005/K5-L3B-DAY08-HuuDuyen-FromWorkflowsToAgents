# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm:
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`):

## 2. Mục tiêu và cách tiếp cận

Nhóm hiểu bài toán thế nào, chia việc ra sao, thứ tự làm bốn shape.

...

## 3. Giải pháp

Mô tả ba shape nhóm viết (workflow, single, orchestrator): mỗi shape đọc gì, quyết định gì, gọi host ra sao. Chỉ rõ ranh giới code / model (tham khảo [docs/architecture.md](../../docs/architecture.md)), cách handoff được sanitize và trace ghi những event nào.

### Shape A — `workflow` (`src/lab8/shapes/workflow.py`)

...

### Shape B — `single` (`src/lab8/shapes/single.py`)

...

### Shape C — `orchestrator` (`src/lab8/shapes/orchestrator.py`)

- **Luồng thực thi:**
  1. Đọc thông tin claim qua `get_claim_view(conn, claim_id)` (chỉ lấy `claim_id`, `principal_id`, `order_id`, `ticket`). Nếu không tìm thấy claim → ghi event `error` và trả `status="failed"` (`error_reason="unknown_claim"`); nếu thiếu `order_id` → gọi `complete(..., purpose="draft")` và trả `status="needs_info"` (`error_reason="missing_order_id"`).
  2. Gọi `complete(budget, seed=seed, purpose="plan", prompt=claim_view["ticket"])` cho bước lập kế hoạch, sau đó dựng gói giao việc bằng `lab8.handoff.make_handoff(...)` và chạy `run_readonly_investigators(conn, budget, handoff, principal_id=...)`.
  3. Kiểm tra `order_view.get("visible")` từ kết quả `lookup_order`: nếu không hợp lệ hoặc ngoài `principal_id` → trả `status="escalated"`.
  4. Lấy báo giá từ kết quả `compute_compensation` (tính từ dữ liệu có cấu trúc `order_view["order"]` và policy hiện hành, bỏ qua số ngày trễ tự khai trong `ticket`), gọi `complete(..., purpose="draft", prompt=f"proposal={proposal}")`.
  5. Nếu `proposal <= 0` → trả `status="denied"` (không gọi `issue_refund`). Nếu `proposal > 0` → gọi `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)` với **quote đầy đủ**; nếu gặp `InjectedCrash` thì ghi event `crash`, gọi `trace.write()` rồi re-raise để giữ đúng hành vi kiểm thử crash; nếu host từ chối hoặc có `conflict` → trả `denied`/`failed`, thành công → trả `resolved`. Mọi nhánh return đều đi qua `common.finish(...)`.
- **Ranh giới Code / Model & Orchestrator / Investigator:**
  - Investigator chỉ được cấp 4 read-only tools (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`), hoàn toàn không có quyền gọi write tool (`issue_refund`, `append_audit`).
  - `MockLLM` (`complete`) chỉ được dùng để mô phỏng chi phí lập kế hoạch (`plan`) và soạn phản hồi (`draft`); mọi quyết định về tiền (`compute_compensation`), quyền sở hữu đơn (`principal_id`), approval, idempotency và trần hoàn tiền theo đơn do code và host (`durability.issue_refund`) quyết định. Orchestrator luôn truyền **quote đầy đủ** để host tự trừ các khoản đã hoàn trước đó trên cùng đơn.
- **Sanitize Handoff & Bảo vệ Trace (`Trace contract v1`):**
  - `make_handoff` và `sanitize` trong `src/lab8/handoff.py` lọc cứng theo allowlist `ALLOWED_FIELDS` và `FACT_KEYS`, truyền `facts={}` (không đưa claim row thô vào `facts`), loại bỏ field ngoài danh sách và ném `HandoffError` nếu phát hiện `CANARY_SECRET_`, `parent_secret`, `raw_headers` hoặc write tool.
  - Trace được ghi mới theo `run_id = make_run_id("orchestrator", claim_id, seed)` ở mọi nhánh kết thúc, gồm các event đã sanitize: `handoff`, `investigator` (`order_view` chỉ gồm 7 trường `ORDER_FIELDS`, `lookup_refund_history`, và `policy_count`), `quote`, và `decision`/`error`/`crash`. Cố ý **không** đọc hoặc ghi vào trace các trường nhạy cảm: `parent_secret`, `raw_headers_json`, SĐT (`phone`), địa chỉ (`address`), tên mặt hàng (`item`) và ghi chú nội bộ (`internal_note`).
- **Kiểm thử bổ sung:** Đã thêm `test_orchestrator_sanitizes_handoff_and_protects_trace` và `test_orchestrator_passes_full_quote_and_survives_crash` trong `src/tests/test_handoff_secret.py` (kiểm tra allowlist handoff, chặn rò rỉ secret/PII, tin order row thay vì ticket ở seed 55, truyền quote đầy đủ ở `C-014`, và phục hồi đúng 1 dòng ledger sau `InjectedCrash` ở `C-012`).

## 4. Kết quả

Đánh giá sau tích hợp tại commit `636b958` (Kiên tổng hợp). Nguồn: `src/reports/benchmark.json`.

| Shape | Pass | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean/p95 steps |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| workflow | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 28.871429 | 4.428571/5 |
| single | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 29.872857 | 4.714286/5 |
| orchestrator | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 57.190000 | 3.714286/4 |
| swarm | 69/70 | 0.985714 | 0.928571 | 0.928571–1.000000 | 0.000816327 | 49.566957 | 2.800000/3 |

Toàn bộ 411 test pass: host 100, student 311. Crash suite chính thức 20/20; 12 ca bổ sung qua `run_claim` kiểm ba điểm crash trên bốn shape đều pass. Không phát hiện secret/PII hoặc approval bypass trong các ca safety đã kiểm; chưa có số liệu hidden.
Đề xuất workflow vì cùng pass 70/70 với single/orchestrator và cost/success thấp nhất. Người điều phối rà soát/chốt `decision_adr.md`. Swarm fail C-002 seed 55, run id `R-swarm-C-002-s55`. Research card R2 và 20 test ablation xác nhận lỗi tin số ngày trong ticket. Chi tiết và lệnh tái lập: `safety_evaluation.md`.

## 5. Khó khăn và cách xử lý

- Windows báo `PermissionError [WinError 5] ... Temp/pytest-of-Admin`; chuyển thư mục tạm pytest bằng `--basetemp=.venv/pytest-host-current` hoặc thư mục test riêng tương ứng.
- Máy ban đầu ở `034c6c4`, chậm 7 commit. Đã fetch và fast-forward đến `0f8b7e6`, có đủ ba shape; giữ lại test và báo cáo của Kiên. Kết quả baseline 0/70 của stub đã được thay bằng lần chạy sau tích hợp.
- Python trên máy là 3.14.6; bộ kiểm tra chạy thành công, nhưng lab công bố hỗ trợ 3.11–3.13 nên cần xác nhận lại môi trường đó nếu dùng để chấm.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

...

## 8. Tài liệu tham khảo

...
