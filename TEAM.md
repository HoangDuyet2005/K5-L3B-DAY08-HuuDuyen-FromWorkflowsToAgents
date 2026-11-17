# Team

## Thông tin nhóm

- Tên nhóm: HuuDuyen
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-HuuDuyen-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/HoangDuyet2005/K5-L3B-DAY08-HuuDuyen-FromWorkflowsToAgents, nhánh `main`, commit chốt điền ở CP5

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Hoàng Thế Duyệt | 2A202603980 |  | HoangDuyet2005 | Điều phối/tích hợp; Shape A `workflow.py`; ADR và báo cáo nhóm |
|   2 | Nguyễn Minh Triết | 2A202603995 |  | minhtriet061203 | Shape B `single.py` (ReAct, tối đa 8 bước) |
|   3 | Lã Quốc Nghị | 2A202603947 |  | quocnghidev | Shape C `orchestrator.py`, handoff và trace |
|   4 | Trần Trung Kiên | 2A202604014 | | ttkien0710 | Safety, kiểm thử liên shape, crash suite và benchmark |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Trần Trung Kiên | Safety/evaluation | `636b958` — test liên shape và bằng chứng sau tích hợp | `src/tests/test_safety_evaluation.py` — 84 test: approval, crash, trace/stdout, cap theo đơn, ticket ablation |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## MSSV_HoTen

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-
