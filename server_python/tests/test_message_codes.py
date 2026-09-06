"""Ràng buộc giữa danh mục thông báo của backend và file dịch của client.

Ba thứ dưới đây rơi ra khỏi mọi loại test khác vì chúng không làm hỏng build,
không làm rớt request, và không hiện ra khi thử bằng ngôn ngữ mặc định:

  * một `raise ApiError(...)` mới quên đặt `code` -> toast ra tiếng Việt giữa
    giao diện tiếng Nhật,
  * gõ nhầm mã -> `message_for` ném KeyError ngay giữa luồng xử lý request,
  * thêm mã ở backend mà quên thêm bản dịch -> người dùng thấy tiếng Việt.

Test này đọc thẳng mã nguồn nên không cần chạy server.
"""

import ast
import json
import re
from pathlib import Path

import pytest
from app.messages import MESSAGES, UnknownMessageCode, message_for

APP_DIR = Path(__file__).resolve().parent.parent / "app"
LOCALES_DIR = Path(__file__).resolve().parent.parent.parent / "client" / "src" / "i18n" / "locales"


def _python_files() -> list[Path]:
    return sorted(p for p in APP_DIR.rglob("*.py") if "__pycache__" not in p.parts)


# `Gap`/`Met` trong matching.py cũng có trường `code`, nhưng mã của chúng nằm ở
# namespace `match` phía client chứ không phải danh mục thông báo — nên chỉ soi
# đúng hai hàm sinh ra response.
MESSAGE_CALLERS = {"ApiError", "ok"}


def _code_literals() -> set[str]:
    """Mã truyền vào `ApiError(code=...)` và `ok(code=...)` trong toàn bộ app."""
    codes: set[str] = set()
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name not in MESSAGE_CALLERS:
                continue
            for kw in node.keywords:
                if kw.arg == "code" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    codes.add(kw.value.value)
    return codes


def test_every_code_used_in_app_exists_in_catalog():
    unknown = sorted(c for c in _code_literals() if c not in MESSAGES)
    assert not unknown, f"Mã không có trong app/messages.py: {unknown}"


def test_unknown_code_fails_loudly():
    """Gõ nhầm mã phải nổ ngay, không được lặng lẽ thành chuỗi rỗng."""
    with pytest.raises(UnknownMessageCode):
        message_for("khong.ton.tai")


def test_every_catalog_message_formats_without_error():
    """Câu có `{...}` mà không được truyền tham số sẽ ném KeyError lúc chạy."""
    for code, template in MESSAGES.items():
        placeholders = set(re.findall(r"\{(\w+)\}", template))
        rendered = message_for(code, {p: "x" for p in placeholders} or None)
        assert rendered, code
        assert "{" not in rendered, f"{code}: còn chỗ trống chưa thay -> {rendered}"


def test_no_api_error_raised_without_code():
    """Mỗi `raise ApiError(...)` phải có `code=` để client dịch được.

    Ngoại lệ duy nhất: `require_admin` nhận câu tuỳ biến từ 8 controller nên
    tra mã ngược qua bảng `_MESSAGE_CODES`.
    """
    allowed_without_code = {("utils/permissions.py", "require_admin")}
    offenders = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)):
                continue
            func = node.exc.func
            if not (isinstance(func, ast.Name) and func.id == "ApiError"):
                continue
            if any(kw.arg == "code" for kw in node.exc.keywords):
                continue
            rel = str(path.relative_to(APP_DIR))
            enclosing = next(
                (
                    n.name
                    for n in ast.walk(tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and n.lineno <= node.lineno <= (n.end_lineno or n.lineno)
                ),
                "?",
            )
            if (rel, enclosing) in allowed_without_code:
                continue
            offenders.append(f"{rel}:{node.lineno} trong {enclosing}()")
    assert not offenders, "ApiError thiếu `code=` (client sẽ không dịch được): " + ", ".join(offenders)


# ---------------------------------------------------------------------------
# Ràng buộc sang phía client
# ---------------------------------------------------------------------------


def _client_error_catalog(lang: str) -> dict:
    path = LOCALES_DIR / lang / "error.json"
    if not path.exists():
        pytest.skip(f"Không có thư mục client ({path})")
    return json.loads(path.read_text(encoding="utf-8"))["server"]


@pytest.mark.parametrize("lang", ["ja", "vi", "en"])
def test_client_has_translation_for_every_backend_code(lang):
    catalog = _client_error_catalog(lang)
    missing = []
    for code in MESSAGES:
        group, leaf = code.split(".", 1)
        if leaf not in catalog.get(group, {}):
            missing.append(code)
    assert not missing, f"[{lang}] thiếu bản dịch cho: {sorted(missing)}"


@pytest.mark.parametrize("lang", ["ja", "vi", "en"])
def test_client_has_no_orphan_code(lang):
    """Bản dịch cho mã đã bị xoá ở backend chỉ làm file phình ra vô ích."""
    catalog = _client_error_catalog(lang)
    orphans = [
        f"{group}.{leaf}" for group, entries in catalog.items() for leaf in entries if f"{group}.{leaf}" not in MESSAGES
    ]
    assert not orphans, f"[{lang}] dư bản dịch: {sorted(orphans)}"


@pytest.mark.parametrize("lang", ["ja", "vi", "en"])
def test_translation_placeholders_match_backend(lang):
    """`{max}` phía Python phải thành `{{max}}` phía i18next, đúng tên."""
    catalog = _client_error_catalog(lang)
    problems = []
    for code, template in MESSAGES.items():
        group, leaf = code.split(".", 1)
        translated = catalog.get(group, {}).get(leaf)
        if translated is None:
            continue
        expected = set(re.findall(r"\{(\w+)\}", template))
        actual = set(re.findall(r"\{\{\s*(\w+)\s*\}\}", translated))
        if expected != actual:
            problems.append(f"{code}: backend {sorted(expected)} vs {lang} {sorted(actual)}")
    assert not problems, problems


# ---------------------------------------------------------------------------
# Mã của phần "còn thiếu gì" (namespace `match` phía client)
# ---------------------------------------------------------------------------

MATCH_CODE_CALLERS = {"Gap", "Met"}


def _match_codes() -> set[str]:
    """Mã truyền vào `Gap(code=...)` / `Met(code=...)` trong matching.py."""
    codes: set[str] = set()
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            if node.func.id not in MATCH_CODE_CALLERS:
                continue
            for kw in node.keywords:
                if kw.arg == "code" and isinstance(kw.value, ast.Constant):
                    codes.add(kw.value.value)
    return codes


def _lookup(catalog: dict, dotted: str):
    node = catalog
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


@pytest.mark.parametrize("lang", ["ja", "vi", "en"])
def test_client_translates_every_gap_and_met_code(lang):
    """Thiếu một mã ở đây thì trang "tôi còn thiếu gì" rơi về câu tiếng Việt.

    Không sập, không báo lỗi — chỉ là giữa giao diện tiếng Nhật bỗng có một
    dòng tiếng Việt. Đúng loại lỗi chỉ lộ ra lúc demo.
    """
    path = LOCALES_DIR / lang / "match.json"
    if not path.exists():
        pytest.skip(f"Không có thư mục client ({path})")
    catalog = json.loads(path.read_text(encoding="utf-8"))

    codes = _match_codes()
    assert codes, "Không tìm thấy mã nào — có phải matching.py đã đổi cấu trúc?"

    missing = [c for c in sorted(codes) if not isinstance(_lookup(catalog, c), str)]
    assert not missing, f"[{lang}] match.json thiếu: {missing}"


@pytest.mark.parametrize("lang", ["ja", "vi", "en"])
def test_client_has_a_label_for_every_language_level(lang):
    """`LANGUAGE_LEVELS` là hợp đồng chung giữa backend và client.

    Backend gửi mã thô (`"business"`), client mới đổi thành nhãn hiển thị. Thêm
    một bậc mới ở `app/models/job.py` mà quên thêm nhãn thì giao diện in ra
    đúng mã thô đó — không sập, không báo lỗi, chỉ là chữ lạ trên màn hình.

    Ba bảng nhãn phải cùng phủ hết: `job.level` (thang tiếng Nhật, có mã JLPT),
    `job.englishLevel` (thang tiếng Anh, không có JLPT), và `resume.level` /
    `resume.englishLevel` (người dùng tự khai trong CV).
    """
    from app.models.job import LANGUAGE_LEVELS

    job_path = LOCALES_DIR / lang / "job.json"
    resume_path = LOCALES_DIR / lang / "resume.json"
    if not job_path.exists():
        pytest.skip(f"Không có thư mục client ({job_path})")

    job = json.loads(job_path.read_text(encoding="utf-8"))
    resume = json.loads(resume_path.read_text(encoding="utf-8"))

    tables = {
        "job.level": job["level"],
        "job.englishLevel": job["englishLevel"],
        "resume.level": resume["level"],
        "resume.englishLevel": resume["englishLevel"],
    }
    missing = [f"{name}.{level}" for name, table in tables.items() for level in LANGUAGE_LEVELS if level not in table]
    assert not missing, f"[{lang}] thiếu nhãn: {missing}"
