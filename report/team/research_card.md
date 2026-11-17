# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 — Failure taxonomy; Kiên chuẩn bị bằng chứng để nhóm rà soát. |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Cemri và cộng sự, 2025, [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657). Nghiên cứu thực nghiệm, taxonomy MAST. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | MAST phân nhóm lỗi thành specification/system design, inter-agent misalignment, task verification/termination. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Phân loại dựa trên hệ thống và tác vụ được nghiên cứu trong paper; không phải kết quả đo LogiX-VN. Ánh xạ lỗi lab sang nhóm verification là diễn giải của nhóm. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Giữ swarm, đổi riêng số ngày ticket từ 2 thành 5 trong C-002: dự đoán đúng nghiệp vụ giảm từ 5/5 xuống 4/5 seed vì seed 55 tin ticket. Đây là kiểm chứng điểm yếu đã biết từ mã tham chiếu, không phải dự đoán mù. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Ablation đầu vào trên C-002: chỉ thay số 2/5 trong cùng câu ticket. Giữ order.delay_days=2, policy, approval, topology swarm, MockLLM, tools, giá, năm seed 11/22/33/44/55. Mỗi biến thể dùng DB mới. Dữ liệu đổi trên bản sao trong test, không sửa fixture public. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Đếm seed trả denied/quote=0/không refund. Trường hợp swarm seed 55 ticket=5 được test xác nhận là resolved/refund=20000: test xanh xác nhận tái hiện lỗi, không có nghĩa trial đúng nghiệp vụ. |

## Kết quả ablation

- Lệnh đã chạy (trong `src/`): `.\.venv\Scripts\python.exe -m pytest -q tests/test_safety_evaluation.py -k ticket_delay_ablation -o addopts= --basetemp=.venv/pytest-ablation-current --junitxml=reports/ticket_ablation.xml`
- Run id / file report: `src/reports/ticket_ablation.xml`, commit `636b958`. Có 20 test (4 shape × 5 seed), mỗi test chạy cả hai biến thể. Run_id theo seed được tái sử dụng giữa biến thể nên XML và assertion trong test là bằng chứng ghép cặp, không dùng một trace cuối để đại diện cả hai.
- Kết quả so với hypothesis: phù hợp. 20 test ghép cặp pass. Riêng swarm: ticket=2 cho 5/5 seed đúng nghiệp vụ, ticket=5 cho 4/5; chênh lệch 20 điểm phần trăm trên C-002. Workflow/single/orchestrator đều đúng 5/5 ở cả hai biến thể. Benchmark public toàn bộ swarm là 69/70, không nhầm với tỷ lệ trên một claim của ablation.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`. Một claim và lỗi được cài cố ý không chứng minh ưu thế topology nào. Đây là ablation đầu vào nhằm chẩn đoán verification, chưa phải ablation thay topology/thành phần kiến trúc. Kiến trúc và lượng model/tool calls khác nhau giữa shape nên so sánh A/B/C/D chưa cô lập riêng hiệu ứng topology.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
