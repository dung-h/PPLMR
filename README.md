# PPLMR — Answer Set Programming mini-project (PPL · Database · OS)

Mini-project này triển khai **3 ứng dụng Answer Set Programming (ASP)** tương ứng với 3 môn học:

- **PPL (Principles of Programming Languages):** phân tích *scope* / *binding* của biến (có chẩn đoán lỗi + hỗ trợ lexical scoping/shadowing/free-variable).
- **Database Systems:** kiểm tra **conflict-serializability** bằng precedence graph; bản mở rộng phân tích **recoverable / cascadeless / strict** khi input có `commit`.
- **Operating Systems:** kiểm tra **safe state** và sinh **safe sequence** theo phong cách *Banker’s algorithm* (kèm atom chẩn đoán khi UNSAT).

Trọng tâm của repo là cách mô hình hóa bằng **facts/rules/constraints**, chạy **Clingo** để lấy stable model, và đọc các predicate đầu ra như một “báo cáo chẩn đoán” thay vì chỉ đúng/sai.

## Cấu trúc thư mục

- `scripts/` — Python runner cho từng ứng dụng (tự sinh file ASP từ templates + chạy Clingo + kiểm tra kỳ vọng).
- `asp/` — các file ASP baseline được runner sinh ra (ví dụ case “baseline”).
- `cases/` — các test case mở rộng theo từng môn:
  - `cases/ppl/` (scope/binding + lexical scoping)
  - `cases/db/` (serializability + isolation/recoverability)
  - `cases/os/` (safe/unsafe states)
- `report/` — mã LaTeX của báo cáo.
- `report.pdf` — bản PDF tổng hợp báo cáo.
- `vendor/tyc/` — (tuỳ chọn) demo tích hợp với frontend/compiler TyC để sinh facts cho PPL.

## Yêu cầu

- Python 3.10+ (khuyến nghị dùng venv)
- Clingo
  - Cách đơn giản (đủ cho runner):
    - `pip install clingo`
  - Nếu bạn có sẵn `clingo` binary trong PATH thì cũng chạy được.

Tuỳ chọn:
- `pip install pymupdf` để dùng `scripts/pdf_visual_reader.py` (render PDF → PNG).
- `pip install antlr4-python3-runtime` nếu chạy demo TyC trong `scripts/ppl_tyc_scope_binding.py`.

## Chạy nhanh (Windows / PowerShell)

Tạo môi trường và cài phụ thuộc tối thiểu:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install clingo
```

Chạy 3 ứng dụng:

```powershell
python scripts\scope_binding.py
python scripts\db_serializability.py
python scripts\os_banker.py
```

Mỗi runner sẽ:
- ghi/ghi đè file ASP tương ứng trong `asp/` và `cases/`
- gọi Clingo để lấy stable model (thường lấy 1 model)
- in stable model + kiểm tra “PASS/FAIL” theo kỳ vọng của từng case

## Ứng dụng 1 — PPL: Scope & Binding

Runner: `scripts/scope_binding.py`

Các predicate tiêu biểu trong output:
- `global_variable/1`, `local_variable/2`
- `in_scope/2`
- `bound_variable/2` (chỉ suy ra khi `type_of(X,int)`)

Predicate chẩn đoán:
- `missing_scope/1`, `untyped_variable/1`, `non_int_type/2`
- `orphan_declaration/2`

Phần nâng cao (lexical scoping):
- `binding/3`, `resolved_use/3`, `free_var/2`, `shadowing/3`

## Ứng dụng 2 — Database: Conflict-Serializability (+ isolation)

Runner: `scripts/db_serializability.py`

Đầu ra chính:
- `edge/2`, `cycle/1`
- `serializable` hoặc `not_serializable`
- `order/2` (khi serializable)

Nếu input có `commit` (`op(I,T,c,none).`) thì bật phân tích mở rộng:
- `rf/5`
- `recoverable` / `not_recoverable` + `recoverable_violation/3`
- `cascadeless` / `not_cascadeless` + `cascadeless_violation/3`
- `strict` / `not_strict` + `strict_violation/3`

## Ứng dụng 3 — OS: Banker safe sequence

Runner: `scripts/os_banker.py`

Đầu ra chính:
- `run/2` (thứ tự chạy), `need/3`, `available/3`

Chẩn đoán khi UNSAT:
- `blocked_initial/1`, `lacks_resource_now/2`, `can_run_now/1`

## Tiện ích: Render PDF

Nếu muốn render `report.pdf` ra ảnh để xem nhanh:

```powershell
pip install pymupdf
python scripts\pdf_visual_reader.py report.pdf --pages 1-3 --zoom 2.0
```

Ảnh sẽ được ghi vào `report/_pdf_pages/` (mặc định).

## Ghi chú

- Repo ưu tiên tính “kiểm chứng tự động”: runner không chỉ chạy Clingo mà còn **so khớp atom kỳ vọng** cho từng case.
- Nếu bạn muốn chạy Clingo trực tiếp trên một file `.lp`, chỉ cần:

```powershell
python -m clingo cases\ppl\global_only.lp 1
```

(Trong đó `1` nghĩa là lấy tối đa 1 stable model.)
