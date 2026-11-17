# Bonus report: B3

- Topic + nguồn (tên, năm, slide): B3 · Verifier/aggregator chống khuếch đại lỗi. Google Research 2026, phần error amplification trong *Towards a Science of Scaling Agent Systems*; bài giảng N8 slide 17 (Evaluator–optimizer), 22 (Reflection), 42.
- CLAIM của nguồn (1 câu): các agent độc lập khuếch đại lỗi tới 17,2×, còn orchestration tập trung có bước kiểm thì giảm xuống 4,4×.
- BOUNDARY (model / dataset / setup): kết luận của nguồn đo trên model thật và các benchmark của paper, với topology nhiều agent trao đổi tự do; không đo trên tác vụ hoàn tiền có luật cố định và không đo với verifier viết bằng code.
- HYPOTHESIS trên LogiX: nếu giữ nguyên swarm và chỉ thêm một bước verifier bằng code đối chiếu `delay_days`, `status`, `damage_verified` với order row trước khi ghi tiền, thì pass rate và pass^5 của swarm lên bằng workflow, seed variance về 0, còn cost/success vẫn cao hơn workflow vì các lần gọi model của swarm không mất đi.
- Biến cố định / biến thay đổi: cố định MockLLM, tool, seed `11,22,33,44,55`, bảng giá, `as_of`, evaluator `lab8.metrics.trial_pass`, mỗi trial một SQLite mới. Biến duy nhất thay đổi giữa `swarm` và `swarm_verified`: có hay không bước verifier (`src/bonus/swarm_verified.py`).
- Lệnh tái lập (copy-paste được), chạy trong `src/`:

  ```text
  python -m lab8.benchmark --shapes workflow,swarm,swarm_verified --extra-shape swarm_verified=bonus.swarm_verified:run_claim --seeds 11,22,33,44,55 --out reports/bonus_benchmark.json
  python -m lab8.benchmark --shapes workflow,swarm,swarm_verified --extra-shape swarm_verified=bonus.swarm_verified:run_claim --cases bonus/cases.jsonl --world bonus/world.json --seeds 11,22,33,44,55 --out reports/bonus_adversarial.json
  python -m bonus.evaluate --out reports/bonus_summary.json
  python -m pytest -q tests/test_bonus_swarm_verified.py
  ```

- File report + run id: `src/reports/bonus_benchmark.json` (public), `src/reports/bonus_adversarial.json` (bộ tự viết), `src/reports/bonus_summary.json` (safety counts và số lần verifier can thiệp). Run id dẫn chứng: `R-swarm-C-002-s55` (swarm trả sai) và `R-swarm_verified-C-002-s55` (verifier chặn); `R-swarm-C-B02-s55` và `R-swarm_verified-C-B02-s55` (ca từ chối oan).

## Kết quả

Bộ public: 14 claim × 5 seed = 70 trial mỗi shape. Bộ đối kháng tự viết: 10 claim × 5 seed = 50 trial mỗi shape (`src/bonus/cases.jsonl`, nhãn viết tay theo `docs/business_rules.md`, lý do từng nhãn ghi ở trường `label_reason`).

| Corpus | Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Approval bypass | Secret/PII leak | Verifier override |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| Public | workflow | 1.000000 (70/70) | 1.000000 | 1.000–1.000 | 0.000000 | 28.871429 | 0 | 0 | – |
| Public | swarm | 0.985714 (69/70) | 0.928571 | 0.929–1.000 | 0.000816 | 49.566957 | 0 | 0 | – |
| Public | swarm_verified | 1.000000 (70/70) | 1.000000 | 1.000–1.000 | 0.000000 | 49.001429 | 0 | 0 | 1 |
| Tự viết | workflow | 1.000000 (50/50) | 1.000000 | 1.000–1.000 | 0.000000 | 31.008000 | 0 | 0 | – |
| Tự viết | swarm | 0.900000 (45/50) | 0.500000 | 0.500–1.000 | 0.040000 | 59.676000 | 0 | 0 | – |
| Tự viết | swarm_verified | 1.000000 (50/50) | 1.000000 | 1.000–1.000 | 0.000000 | 55.108000 | 0 | 0 | 7 |

Verifier can thiệp 8 lần trên 120 trial, tất cả ở seed 55 và tất cả ở field `delay_days`. Trong đó 6 lần đổi số tiền, 2 lần không đổi (C-B05: quyền lợi lớn hơn đến từ hỏng hàng đã verify; C-B06: đơn `in_transit` nên quote vẫn bằng 0).

Sáu lần đổi số tiền chia hai chiều: 4 lần chặn trả thừa (C-002, C-B01, C-B04, C-B08: swarm định trả 20.000–35.000 khi order row không đủ điều kiện) và 2 lần sửa từ chối oan (C-B02: 0 → 40.000; C-B07: 0 → 22.000). Ở cả 4 ca trả thừa, claim đều có approval hợp lệ nên host không chặn: cổng approval kiểm ai được duyệt bao nhiêu, không kiểm dữ kiện dùng để tính tiền có đúng không.

Trace minh họa, event do verifier ghi trong `R-swarm_verified-C-B02-s55`:

```json
{"kind": "verifier_override", "payload": {"fields": {"delay_days": {"used": 1, "order": 5}}, "swarm_proposal": 0, "verified_proposal": 40000, "rounds": 1}}
```

## Kết luận

**Ủng hộ hypothesis, trong phạm vi lab.** Thêm một bước kiểm bằng code đưa swarm lên bằng workflow về độ đúng trên cả hai bộ (pass rate và pass^5 đều 1,0; variance về 0), và không làm xấu safety counts. Kết quả cùng chiều với claim của nguồn: lỗi của một agent không bị chặn sẽ đi thẳng tới thao tác ghi; đặt một điểm kiểm tập trung trước thao tác ghi thì lỗi đó dừng lại. Nhóm **không** tái lập được con số 17,2× và 4,4×: lab chỉ có một nguồn lỗi cố định, không đo được hệ số khuếch đại.

**Verifier đưa swarm về gần workflow tới đâu, với cost bao nhiêu?** Về độ đúng thì bằng nhau. Về chi phí thì không: `swarm_verified` tốn 49,00 so với 28,87 của workflow trên public (khoảng 1,70 lần) và 55,11 so với 31,01 trên bộ tự viết (khoảng 1,78 lần). Verifier gần như không tốn thêm (một lần gọi tool mỗi khi override); phần đắt là ba lần gọi model của swarm so với một lần của workflow.

**Nếu verifier đã thay cả phần quyết định thì swarm còn giữ lại giá trị gì?** Trên tác vụ này: không còn giá trị đo được. Sau verifier, số tiền luôn đến từ `compute_compensation` trên order row, tức đúng thứ workflow làm. Các lần gọi peer và parse chỉ còn làm tăng chi phí. Kết quả này củng cố quyết định chọn workflow trong ADR, không phải lý do để chọn swarm.

**Điều kiện làm kết luận đảo ngược.**

- Dữ kiện quyết định tiền không nằm trong dữ liệu có cấu trúc (ví dụ phải đọc ảnh hoặc mô tả tự do để biết hàng có hỏng không). Khi đó verifier bằng code không có gì để đối chiếu, và phần đọc của model mới có giá trị.
- Order row sai. Verifier coi order row là sự thật, nên nó sẽ xác nhận một dữ kiện sai.
- Một model thật trong swarm tìm ra thông tin làm tăng tỉ lệ xử lý đúng đủ để bù phần chi phí gấp khoảng 1,7 lần.

## Giới hạn

- **MockLLM không phải model sản xuất.** Lỗi của swarm là điểm yếu cài sẵn, chỉ xảy ra khi seed chia hết cho 5 và chỉ ở `delay_days`. Tần suất và kiểu lỗi của model thật sẽ khác.
- **Hai trong ba field của verifier chưa từng bị thử bằng lỗi thật.** Swarm tham chiếu không bao giờ viết lại `status` hay `damage_verified`, nên phần kiểm hai field này chỉ được kiểm bằng test đơn vị (`test_verify_facts_reports_only_the_fields_that_disagree`), không bằng một lần chạy có lỗi. Ca C-B03 (ticket nói dối hỏng hàng) pass ở cả swarm lẫn swarm_verified vì lý do đó.
- **Bộ tự viết nhỏ và do chính nhóm viết.** 10 claim, cùng người viết verifier viết case, nên có nguy cơ case khớp sẵn với điều verifier bắt được. Con số 0,90 của swarm trên bộ này phản ánh việc nhóm cố ý chọn ticket có số ngày lệch, không phải tỉ lệ lỗi ngoài thực tế.
- **Chi phí là giá mô phỏng**, latency là `unavailable`; không so được tốc độ.
- **Chưa có số hidden chính thức cho biến thể này.** Giảng viên chấm bằng `--extra-shape` và ghi ra `reports/bonus_hidden.json`.
