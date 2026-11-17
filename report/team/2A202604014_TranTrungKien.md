# Báo cáo cá nhân — Trần Trung Kiên

## 1. Thông tin thành viên

- Họ tên: Trần Trung Kiên
- MSSV: 2A202604014
- Email: ttkpro07102005@gmail.com (theo cấu hình Git của máy)
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

Codex hỗ trợ đọc contract, viết test, chạy công cụ và soạn báo cáo từ output thực tế. Đã kiểm tra tự động bằng pytest và CLI chính thức. Trước khi nộp, cá nhân cần tự đọc/giải thích test, chạy lại các lệnh trong `safety_evaluation.md` và xác nhận nội dung; không coi bản nháp này là lời xác nhận đã tự kiểm tra thủ công.

## 6. Tự đánh giá

Đã hoàn thành kiểm thử public sau tích hợp và có commit kỹ thuật kèm bằng chứng. Đề xuất workflow vì đạt 70/70 và cost/success thấp nhất (28.871429 VND mô phỏng). Chưa có `student_drop/` nên chưa đo hidden; public pass không bảo đảm hidden đạt ngưỡng. Cần cá nhân rà soát nội dung trước khi nộp; nhóm chốt ADR và các báo cáo của thành viên còn lại.
