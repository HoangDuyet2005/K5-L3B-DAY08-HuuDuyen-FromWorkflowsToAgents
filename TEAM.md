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
| Lã Quốc Nghị | Orchestrator/handoff | `90141f7` — Shape C orchestrator | `src/tests/test_handoff_secret.py::test_orchestrator_sanitizes_handoff_and_protects_trace`, `test_orchestrator_passes_full_quote_and_survives_crash` |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603947_LaQuocNghi

### Phần việc phụ trách

- Shape C (`src/lab8/shapes/orchestrator.py`), lọc `handoff` theo allowlist và bảo vệ `trace` theo `Trace contract v1`.

### Đóng góp cụ thể

- Cài đặt `run_claim` trong `src/lab8/shapes/orchestrator.py` (commit `90141f7`).
- Thêm 2 test trong `src/tests/test_handoff_secret.py`: `test_orchestrator_sanitizes_handoff_and_protects_trace`, `test_orchestrator_passes_full_quote_and_survives_crash`.
- Viết phần giải pháp Shape C trong `report/team/group_report.md` và báo cáo cá nhân `report/team/2A202603947_LaQuocNghi.md`.

### Bằng chứng

- Commit `90141f7` trên nhánh `task/quocnghidev`; `.venv/bin/python -m pytest -q` (`79 passed`) và `.venv/bin/python -m pytest -q -m student -o addopts= -k orchestrator` (`62 passed`).

## MSSV_HoTen

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-
