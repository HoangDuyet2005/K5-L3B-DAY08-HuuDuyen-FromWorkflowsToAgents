# Báo cáo cá nhân — Trần Trung Kiên

## 1. Thông tin thành viên

- Họ tên: Trần Trung Kiên
- MSSV: 2A202604014
- Email:
- GitHub: ttkien0710

## 2. Phần việc phụ trách

Safety, kiểm thử liên shape, chạy crash suite/benchmark và tổng hợp bằng chứng cho ADR, research card, báo cáo nhóm.

## 3. Đóng góp cụ thể

- Bổ sung `src/tests/test_safety_evaluation.py`: 21 kịch bản × 4 shape = 84 test, gồm approval sai và retry, ba điểm crash, trace/stdout ở nhiều nhánh, top-up rồi claim mới, ticket ablation.
- 21 test swarm vào cổng host; 63 test A/B/C dùng marker student. Không skip/xfail để che shape chưa làm.
- Test chỉ biến đổi database/bản sao dữ liệu tạm; không sửa policy, durability, metrics hay fixture public.
- Đã lấy đủ ba shape từ GitHub tại `0f8b7e6`, chạy kiểm thử sau tích hợp, sinh báo cáo bằng CLI và tổng hợp trong `safety_evaluation.md`; chuẩn bị research card R2 với giới hạn rõ ràng.
- Commit kỹ thuật: `636b958` — `test: add cross-shape safety evaluation and integrated evidence`. Code shape của đồng đội giữ nguyên.

## 4. Bằng chứng

- `src/reports/integrated_tests.xml`: toàn bộ 411 test pass.
- `src/reports/safety_host.xml`: 100 passed, 311 deselected.
- `src/reports/safety_student.xml`: 311 passed, 100 deselected.
- `src/reports/crash.json`: 20/20 cho suite chính thức; test bổ sung kiểm đủ ba điểm crash và resume hai lần qua `run_claim` trên cả bốn shape, 12/12 ca pass.
- `src/reports/benchmark.json`: bốn shape × 14 claim × 5 seed; swarm 69/70, A/B/C đều 70/70.
- `src/reports/ticket_ablation.xml`: 20 test ghép cặp pass, tái hiện lỗi ticket gây refund sai ở swarm seed 55 và xác nhận A/B/C bỏ qua số ngày sai trong ticket.
- Run id lỗi public: `R-swarm-C-002-s55`.

## 5. Công cụ AI đã dùng

- **Công cụ:** OpenAI Codex và Google Antigravity (Gemini).
- **Phần việc có dùng AI:**
  - Gợi ý các ca đột biến dữ liệu approval (thiếu ID, ID rác, hết hạn, bị thu hồi, tiền 0/âm, sai claim) và dựng khung `@pytest.mark.parametrize` cho `test_safety_evaluation.py`.
  - Hỗ trợ tra cứu taxonomy lỗi của bài báo MAST (NeurIPS 2025) để điền `research_card.md`.
  - Hỗ trợ định dạng bảng Markdown từ output benchmark và test run.
- **Cách tự kiểm chứng:**
  - Tự rà soát toàn bộ assertion của 84 test case, bảo đảm test chỉ thao tác trên DB tạm và không sửa file cấm của hệ thống.
  - Tự chạy kiểm thử trực tiếp trên terminal: test safety pass 21/21 ở cổng host, 63/63 ở student markers, toàn bộ repo pass 411/411.
  - Tự chạy toàn bộ file bằng chứng trong `src/reports/` (`crash.json`, `benchmark.json`, XML) bằng CLI từ code thật sau tích hợp, không nhờ AI bịa số liệu.

## 6. Tự đánh giá

  - Hoàn thành tương đối tốt phần việc được giao, nộp đúng hạn toàn bộ test safety và số liệu benchmark để nhóm kịp thời làm ADR và báo cáo chung.
  - Chủ động thiết kế các ca test biên phức tạp (approval, crash, chống leak secret/PII), giữ kỷ luật kỹ thuật tốt.
  - Phối hợp và hỗ trợ đồng đội tốt trong khâu tích hợp và đối soát lỗi.

  - Kỹ năng xử lý lỗi môi trường (như quyền ghi thư mục tạm trên Windows) ban đầu còn chậm, mất nhiều thời gian gỡ lỗi.
  - Cần chủ động trao đổi và kéo cập nhật từ nhánh chung sớm hơn để giảm bớt áp lực đồng bộ ở cuối buổi.
