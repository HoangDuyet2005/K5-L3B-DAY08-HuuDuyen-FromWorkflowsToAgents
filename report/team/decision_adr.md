# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 636b958
- Run id dẫn chứng: R-workflow-C-001-s11; R-workflow-C-014-s55; đối chứng lỗi R-swarm-C-002-s55 (src/reports/benchmark.json)
- Pass rate / pass^5 / seed min-max / variance: public 1.0 / 1.0 / 1.0–1.0 / 0.0 (70/70 trial)
- Cost per success (mô phỏng, VND): 28.87142857142857
- Crash safety: 20/20 suite chính thức (src/reports/crash.json); cả 3 điểm crash qua run_claim của workflow pass và resume hai lần không duplicate (src/reports/integrated_tests.xml)
- Secret leak / approval bypass: không phát hiện trong các ca public/safety đã kiểm; chưa có số đếm hidden chính thức

Bản đề xuất dựa trên đánh giá do Kiên chuẩn bị sau tích hợp. Người điều phối (Hoàng Thế Duyệt) đã rà soát và cả nhóm thống nhất chọn `workflow`.

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Workflow, single và orchestrator đều đạt 70/70 trên cùng 14 claim và năm seed. Workflow có cost/success 28.871429, thấp hơn single 29.872857 và orchestrator 57.19 VND mô phỏng. Quy trình claim có luật cố định, số tiền và approval do code quyết định; workflow đáp ứng tập public với mức tự chủ thấp nhất trong các shape đang có.

## Có đáng đổi lấy multi-agent không

Chưa có lợi ích pass rate public để bù chi phí cao hơn của B/C. Swarm đạt 69/70, pass^5=0.928571 và variance=0.000816327 vì lỗi cố ý ở C-002 seed 55. Cần đánh giá lại nếu hidden/tác vụ mới đòi hỏi truy vấn linh hoạt, nhiều nhánh điều tra và B/C tăng thành công đủ để bù chi phí. Các shape khác nhau cả số model/tool calls; không kết luận topology đơn thuần gây chênh lệch này.

## Trace và bằng chứng

Workflow ghi claim (found/has_order_id), lookup_order đã lọc, quote, issue_refund (ok/reason/conflict), decision và error khi cần. Không ghi ticket, claim/order thô, parent_secret, headers, SĐT, địa chỉ, tên hàng hay ghi chú nội bộ. Test safety kiểm trace mới, run_id, kết quả, các file cùng run_id và stdout/stderr. Không tuyên bố scanner chứng minh an toàn cho file tùy ý ngoài phạm vi quét; việc review code bổ sung cho kiểm tra tự động.

## Giới hạn

MockLLM không phải model sản xuất; chi phí mô phỏng, latency `unavailable`. Public pass không bảo đảm hidden pass rate ≥0.75. Coach phát gói hidden cho nhóm để tự kiểm trước demo. Kết quả tự chạy trên gói này: workflow, single, orchestrator đều 1.000; swarm 0.970 (40 claim × 5 seed). Đây chỉ là tự kiểm, không thay thế kết quả chính thức; pass rate hidden chính thức do grader của giảng viên chấm, không có số nào trong repo. Môi trường kiểm thử là Python 3.14.6; lab công bố hỗ trợ 3.11–3.13. Không sửa JSON để đạt ngưỡng.
