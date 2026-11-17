# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: HuuDuyen (lớp L3B)
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`):

## 2. Mục tiêu và cách tiếp cận

**Bài toán.** LogiX-VN nhận claim hoàn phí vận chuyển. Nhóm cài cùng một quy trình xử lý claim theo bốn kiến trúc (shape) có chung chữ ký `run_claim`, đo chúng trên cùng claim, cùng seed, cùng bảng giá, rồi chọn kiến trúc ít tự chủ nhất mà vẫn làm đúng việc. Điều nhóm coi là cốt lõi của bài không phải "shape nào thông minh hơn" mà là ranh giới: tiền, approval và chống ghi trùng do code và host quyết; model chỉ đọc và soạn chữ; chữ trong ticket là dữ liệu người dùng, không phải lệnh.

**Nguyên tắc chung cả ba shape tuân theo.**

- Nguồn sự thật là order row và policy hiện hành. Số ngày trễ hay câu lệnh ghi trong ticket không được dùng để tính tiền.
- Số tiền lấy từ `compute_compensation`. MockLLM không quyết số tiền.
- Quote dương thì luôn gọi `durability.issue_refund` với **quote đầy đủ**; host tự kiểm approval, trần theo đơn và idempotency. Shape không tự trừ phần đã hoàn và không tự từ chối thay host.
- Mọi nhánh trả `RunResult` qua `common.finish()` và ghi trace mới. Trace chỉ chứa view đã qua allowlist.
- Truyền `crash_at` vào `issue_refund` và không nuốt `InjectedCrash`.

**Chia việc.** Nhóm 4 người chia theo shape và theo phần kiểm thử, mỗi người sở hữu một file để làm song song và không sửa chồng lên nhau:

| Thành viên | Phần phụ trách |
| --- | --- |
| Hoàng Thế Duyệt | Shape A `workflow.py`; tích hợp các nhánh; ADR và ghép báo cáo nhóm |
| Nguyễn Minh Triết | Shape B `single.py` |
| Lã Quốc Nghị | Shape C `orchestrator.py`, handoff và trace |
| Trần Trung Kiên | Safety, kiểm thử liên shape, crash suite và benchmark |

**Thứ tự làm bốn shape.**

1. Shape D `swarm` có sẵn trong starter; cả nhóm đọc `swarm_reference.py` để thống nhất cách dựng `RunResult` và ghi trace.
2. Shape A `workflow` làm trước, vì đây là shape ít tự chủ nhất và xác lập luồng chuẩn: đọc claim → kiểm đơn → tính quote → gọi host.
3. Shape B `single` và Shape C `orchestrator` làm song song trên nhánh riêng, mỗi người tự kiểm bằng ma trận student của shape mình.
4. Gộp ba nhánh vào `main`, chạy lại toàn bộ ma trận student và cổng host trước khi đẩy, rồi mới chạy crash suite và benchmark trên cả bốn shape.

## 3. Giải pháp

Mô tả ba shape nhóm viết (workflow, single, orchestrator): mỗi shape đọc gì, quyết định gì, gọi host ra sao. Chỉ rõ ranh giới code / model (tham khảo [docs/architecture.md](../../docs/architecture.md)), cách handoff được sanitize và trace ghi những event nào.

### Shape A — `workflow` (`src/lab8/shapes/workflow.py`)

- **Luồng thực thi (thứ tự cố định trong code, không có vòng lặp):**
  1. Đọc claim qua `get_claim_view(conn, claim_id)`. Không tìm thấy claim → `status="failed"` (`error_reason="unknown_claim"`).
  2. Thiếu `order_id` → `status="needs_info"`. Shape không đoán mã đơn từ chữ trong ticket.
  3. `lookup_order(conn, order_id, principal_id)` theo principal của claim. Không thấy đơn hoặc đơn của principal khác → `status="escalated"`.
  4. `compute_compensation(conn, order_view["order"])` tính quote từ order row và policy hiện hành. Quote bằng 0 → `status="denied"`, `proposal_amount=0`, không gọi host.
  5. Quote dương → `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)` với **quote đầy đủ**. Host từ chối → `denied` (host tự ghi audit `policy_denied`), lệch số đã commit → `failed`, thành công → `resolved`. Ở cả ba trường hợp `proposal_amount` vẫn là quote đầy đủ.
  6. Mọi nhánh kết thúc qua cùng một hàm `done(...)`, hàm này gọi `common.finish(...)`.
- **Ranh giới Code / Model:**
  - Code quyết toàn bộ: thứ tự bước, quyền xem đơn theo principal, số tiền và việc gọi host.
  - `MockLLM` chỉ được gọi **một lần** ở cuối (`purpose="draft"`) để soạn câu trả lời. Prompt chỉ gồm `status` và `proposal`, không chứa ticket, nên chữ trong ticket không có đường nào tác động tới kết quả.
  - Shape không tự kiểm approval, không tự trừ phần đơn đã hoàn; hai việc đó thuộc host trong `issue_refund`.
- **Crash và lỗi ngoài dự kiến:**
  - `InjectedCrash` được bắt riêng và ném lại nguyên vẹn, để crash mô phỏng đi ra ngoài (T12).
  - Lỗi khác được bắt và trả `status="failed"` kèm trace, vì `run_claim` không được ném exception ra grader. Trace chỉ ghi tên loại lỗi, không ghi message, để không vô tình mang dữ liệu thô vào trace.
- **Trace:**
  - Các event: `claim` (chỉ `found` và `has_order_id`), `lookup_order` (view allowlist của tool), `quote`, `issue_refund` (`ok`, `reason`, `conflict`), `decision`.
  - Cố ý **không** ghi: nội dung ticket, `principal_id`, claim row và order row thô (nơi có `parent_secret`, header, SĐT, địa chỉ, ghi chú nội bộ, tên hàng).
- **Kiểm thử bổ sung:** `src/tests/test_workflow_shape.py` kiểm các ca ma trận public chưa phủ: claim không tồn tại, store hỏng vẫn trả `failed` có trace, trace của 12 claim public không chứa ticket hay secret, C-002 (ticket ghi trễ 5 ngày, order ghi 2) bị từ chối ở cả 5 seed, và workflow chỉ có đúng một lần gọi model.

### Shape B — `single` (`src/lab8/shapes/single.py`)

- **Luồng thực thi:**
  1. Đọc claim qua `get_claim_view(conn, claim_id)`. Không tìm thấy claim → `status="failed"` (`error_reason="unknown_claim"`); thiếu `order_id` → `status="needs_info"`, không vào vòng lặp.
  2. Chạy vòng ReAct bằng `lab8.runtime.run_react(..., max_steps=8, worker=True)`. Hàm `decide` chọn tool đọc theo thứ tự `lookup_order` → `compute_compensation`, rồi trả `final`. Mỗi bước có một lời gọi MockLLM (`purpose="react"`) được cộng vào `Budget`, để chi phí so sánh được với các shape khác.
  3. `lookup_order` không thấy đơn hoặc đơn của principal khác → `decide` trả `final` với `status="escalated"`.
  4. Sau vòng lặp, quote lấy từ kết quả `compute_compensation` trên order row. Quote bằng 0 → `status="denied"`, không gọi host.
  5. Quote dương → **code của shape**, không phải model, gọi `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)` với **quote đầy đủ**. Host từ chối → `denied`, conflict → `failed`, thành công → `resolved`. Gặp `InjectedCrash` thì ghi event `crash`, ghi trace rồi ném lại. Mọi nhánh kết thúc qua `common.finish(...)`.
- **Ranh giới Code / Model:**
  - Model chỉ được chọn tool đọc. `run_react` chạy với `worker=True`, nên mọi tool ngoài danh sách đọc bị `ToolRejected`; write tool (`issue_refund`, `append_audit`) bị chặn ở `dispatch` bất kể cờ.
  - Số tiền do `compute_compensation` tính từ order row, không lấy số ngày trễ trong ticket.
  - Vòng lặp dừng cứng ở 8 bước; hết bước mà chưa có quote thì trả `failed`.
- **Trace:** các event `claim` (`claim_id`, `has_order_id`), `tool` (tên tool, `visible`/`reason` hoặc số tiền quote và `clause_ids`), `react` (lý do dừng vòng lặp), `decision`, và `crash` khi có. Cố ý **không** ghi ticket, claim row thô (có `parent_secret`, header) và order row thô (SĐT, địa chỉ, tên hàng, ghi chú nội bộ).
- **Nhận xét thiết kế:** `decide` đi theo thứ tự tool cố định, nên trên bộ đo của lab single cư xử gần như workflow, chỉ tốn thêm các lời gọi model trong vòng lặp (cost/success 29.87 so với 28.87 của workflow). Mức tự chủ thật của shape này chỉ đo được khi thay MockLLM bằng một model được tự chọn tool.
- **Kiểm thử bổ sung:** `src/tests/test_single_shape.py` (3 test): C-002 bị từ chối ở cả 5 seed dù ticket ghi trễ 5 ngày; chạy lại C-001 với seed khác vẫn một dòng ledger 35.000; trace đúng contract, không chứa secret, PII hay ticket, và số lời gọi model không quá 8 + 1.

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

Tại thời điểm tích hợp (commit `0f8b7e6`): host 100 test, student 311 test, tổng 411 pass. Hiện tại, sau khi thêm test bonus B3: host 161 test (gồm 61 test bonus), student 311 test, tổng 472 pass. Crash suite chính thức 20/20; 12 ca bổ sung qua `run_claim` kiểm ba điểm crash trên bốn shape đều pass. Không phát hiện secret/PII hoặc approval bypass trong các ca safety đã kiểm; pass rate hidden chính thức do giảng viên chấm; số tự kiểm trên gói coach phát được nêu trong `report/team/decision_adr.md`.
Đề xuất workflow vì cùng pass 70/70 với single/orchestrator và cost/success thấp nhất. Người điều phối rà soát/chốt `decision_adr.md`. Swarm fail C-002 seed 55, run id `R-swarm-C-002-s55`. Research card R2 và 20 test ablation xác nhận lỗi tin số ngày trong ticket. Chi tiết và lệnh tái lập: `safety_evaluation.md`.

## 5. Khó khăn và cách xử lý

- Windows báo `PermissionError [WinError 5] ... Temp/pytest-of-Admin`; chuyển thư mục tạm pytest bằng `--basetemp=.venv/pytest-host-current` hoặc thư mục test riêng tương ứng.
- Máy ban đầu ở `034c6c4`, chậm 7 commit. Đã fetch và fast-forward đến `0f8b7e6`, có đủ ba shape; giữ lại test và báo cáo của Kiên. Kết quả baseline 0/70 của stub đã được thay bằng lần chạy sau tích hợp.
- Python trên máy là 3.14.6; bộ kiểm tra chạy thành công, nhưng lab công bố hỗ trợ 3.11–3.13 nên cần xác nhận lại môi trường đó nếu dùng để chấm.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`; chi phí là giá mô phỏng trong `src/config/pricing.yaml`, không phải hóa đơn API.

**Giới hạn của kết quả.**

- **Variance bằng 0 là do cách cài, không phải bằng chứng model ổn định.** Ở cả ba shape nhóm viết, thứ tự gọi tool và số tiền do code quyết; lời gọi MockLLM chỉ tính chi phí và soạn chữ. Vì vậy kết quả không thể dao động theo seed. Với một model thật được quyền chọn tool, pass rate và variance của `single` và `orchestrator` phải đo lại.
- **Bộ public nhỏ.** 14 claim × 5 seed = 70 trial mỗi shape. Ba shape cùng đạt 70/70 nên bộ này không phân biệt được chúng về độ đúng; khác biệt đo được chỉ nằm ở chi phí và số bước.
- **So sánh chi phí chưa tách riêng topology.** Các shape khác nhau cả số lần gọi model lẫn số lần gọi tool, nên không kết luận chênh lệch cost/success chỉ do kiến trúc.
- **Crash suite chính thức chỉ kiểm host và swarm.** Crash trên ba shape của nhóm được kiểm qua T12 và các ca bổ sung trong `src/tests/test_safety_evaluation.py`, không phải qua `src/reports/crash.json`.
- **Môi trường.** Số liệu trong `src/reports/` được sinh trên Python 3.14.6 (xem mục 5). Người điều phối đã chạy lại bộ test và hai lệnh sinh report trên Python 3.11.9, nằm trong dải lab hỗ trợ: host 100 passed, student 311 passed, crash 20/20, pass rate và pass^5 của bốn shape trùng với file đã nộp.

**Hướng cải thiện.**

- `single.py` và `orchestrator.py` chưa bắt lỗi ngoài dự kiến; nếu gặp dữ liệu lạ, `run_claim` ném exception và trial bị chấm fail. Nên bọc như `workflow.py`: trả `failed` kèm trace, và vẫn để `InjectedCrash` đi ra ngoài.
- Thêm claim đối kháng tự viết (ticket nói quá, nói thiếu, nhiều con số trong một câu) với nhãn viết tay, để bộ đo phân biệt được ba shape.

**Điều kiện làm quyết định chọn `workflow` thay đổi.**

- Nghiệp vụ cần điều tra linh hoạt: số bước và nguồn dữ liệu phải đọc thay đổi theo từng claim, không cố định được trong code.
- Ticket mơ hồ đến mức cần model quyết định có hỏi thêm khách hay không, và việc đó làm tăng tỉ lệ xử lý đúng.
- `single` hoặc `orchestrator` đạt pass rate cao hơn `workflow` trên một bộ đo lớn hơn, với mức tăng đủ bù phần chi phí cao hơn (orchestrator hiện đắt gấp khoảng hai lần trên bộ public).

## 8. Tài liệu tham khảo

- Tài liệu của lab trong repo: `README.md`, `RULES.md`, `CHECKPOINTS.md`, `RUBRIC.md`, `docs/business_rules.md`, `docs/contracts.md`, `docs/architecture.md`, `docs/metrics.md`.
- Code tham chiếu trong starter: `src/lab8/shapes/swarm_reference.py`, `src/lab8/durability.py`, `src/lab8/handoff.py`, `src/lab8/runtime.py`.
- Cemri và cộng sự (2025), *Why Do Multi-Agent LLM Systems Fail?* (MAST) — nguồn của phiếu nghiên cứu R2; thông tin trích dẫn đầy đủ trong `report/team/research_card.md`.
- Bài giảng N8 "From Workflows to Agents" của khóa AI20K K5.
