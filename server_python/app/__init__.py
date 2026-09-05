"""Backend Fuurin (FastAPI).

Chan som phien ban Python qua cu: models dung cu phap `str | None` (PEP 604),
duoc Pydantic danh gia ngay luc tao class, nen tren Python 3.9 se no ra
`TypeError: unsupported operand type(s) for |` — mot thong bao khong he goi y
nguyen nhan that. Bao loi ro rang ngay tai day thay vi de nguoi dung tu doan.
"""

import sys

MINIMUM_PYTHON = (3, 10)

if sys.version_info < MINIMUM_PYTHON:
    raise RuntimeError(
        f"Fuurin backend can Python >= {'.'.join(map(str, MINIMUM_PYTHON))}, "
        f"dang chay {sys.version.split()[0]}. Xem muc 3.2 trong README."
    )
