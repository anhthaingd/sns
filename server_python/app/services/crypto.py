"""Mã hoá nội dung tin nhắn riêng trước khi ghi xuống database.

Vì sao cần
----------
Trước đây `chats.content` và `newestmessages.content` nằm trong MongoDB dưới
dạng chữ thường. Ai đọc được database — một bản backup bị lộ, một người có
quyền vào server, hay chính lập trình viên mở Compass lên xem — là đọc được
toàn bộ tin nhắn riêng của mọi người. Quyền truy cập ở tầng API không giúp gì
cho tình huống đó, vì nó bị đi vòng hoàn toàn.

Ở đây dùng **AES-256-GCM**: vừa giấu nội dung (confidentiality) vừa phát hiện
nếu ai đó sửa bản mã (authenticity). Mỗi tin có một `nonce` 12 byte ngẫu nhiên
riêng — dùng lại nonce với cùng một khoá là phá vỡ hoàn toàn GCM.

Dạng lưu trong DB::

    enc:v1:<base64( nonce(12 byte) || ciphertext || tag(16 byte) )>

Tiền tố `enc:v1:` có hai việc:

* **Tương thích ngược** — tin nhắn cũ (chữ thường, không có tiền tố) vẫn đọc
  được bình thường, không cần chạy migration mới xem lại được lịch sử.
* **Đổi thuật toán về sau** — thêm `enc:v2:` mà không phải đoán mò định dạng.

Giới hạn phải nói thẳng
-----------------------
Đây là mã hoá **khi lưu trữ** (at rest), KHÔNG phải mã hoá đầu-cuối (E2EE).
Máy chủ giữ khoá, nên máy chủ vẫn đọc được nội dung khi xử lý request — bắt
buộc phải thế, vì chính máy chủ là bên chuyển tiếp tin nhắn qua socket và dựng
dòng xem trước trong danh sách hội thoại.

Cụ thể, cái này **có** chống: lộ bản dump DB, lộ ổ đĩa, người có quyền đọc DB
nhưng không có quyền đọc biến môi trường của tiến trình.
**Không** chống: máy chủ bị chiếm quyền hoàn toàn (kẻ tấn công lấy luôn khoá).
Muốn chống cả trường hợp đó thì phải làm E2EE — khoá sinh và giữ trong trình
duyệt, và khi đó máy chủ hết khả năng hiển thị dòng xem trước.

Việc "chỉ hai người trong cuộc hội thoại mới xem được" là một lớp khác, nằm ở
`app/controllers/chat.py` và `app/sockets/handlers.py`.
"""

import base64
import hashlib
import logging
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config.settings import ACCESS_TOKEN_SECRET, MESSAGE_ENCRYPTION_KEY

logger = logging.getLogger("fuurin.crypto")

PREFIX = "enc:v1:"
NONCE_SIZE = 12


def _load_key() -> bytes:
    """32 byte khoá AES-256.

    Có `MESSAGE_ENCRYPTION_KEY` thì dùng thẳng. Không có thì dẫn xuất từ
    `ACCESS_TOKEN_SECRET` để dev `docker compose up` là chạy — nhưng dẫn xuất
    chứ không dùng lại nguyên xi, để một khoá không bao giờ gánh hai vai.
    """
    raw = (MESSAGE_ENCRYPTION_KEY or "").strip()
    if raw:
        try:
            key = base64.b64decode(raw, validate=True)
        except Exception:
            key = raw.encode("utf-8")
        if len(key) == 32:
            return key
        # Chuỗi dài/ngắn tuỳ ý vẫn dùng được, nhưng phải băm về đúng 32 byte.
        logger.warning("MESSAGE_ENCRYPTION_KEY không phải 32 byte, sẽ băm về 32 byte bằng SHA-256")
        return hashlib.sha256(key).digest()

    return hashlib.sha256(f"fuurin-message-encryption:{ACCESS_TOKEN_SECRET}".encode()).digest()


_aesgcm = AESGCM(_load_key())


def encrypt_text(plaintext: str | None) -> str | None:
    """Chuỗi thường -> `enc:v1:<base64>`. `None`/rỗng giữ nguyên."""
    if not plaintext:
        return plaintext
    if plaintext.startswith(PREFIX):
        # Đã mã hoá rồi — không bọc thêm một lớp nữa.
        return plaintext
    nonce = os.urandom(NONCE_SIZE)
    sealed = _aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return PREFIX + base64.b64encode(nonce + sealed).decode("ascii")


def decrypt_text(stored: str | None) -> str | None:
    """`enc:v1:<base64>` -> chuỗi thường.

    Giá trị không có tiền tố được trả về nguyên vẹn: đó là tin nhắn từ trước
    khi có mã hoá, và người dùng vẫn phải đọc lại được lịch sử của mình.

    Giải mã hỏng (sai khoá, dữ liệu bị sửa) KHÔNG được làm sập cả trang chat —
    chỉ tin đó hiện chuỗi rỗng, và log lại để còn lần ra.
    """
    if not stored or not stored.startswith(PREFIX):
        return stored
    try:
        blob = base64.b64decode(stored[len(PREFIX) :], validate=True)
        nonce, sealed = blob[:NONCE_SIZE], blob[NONCE_SIZE:]
        return _aesgcm.decrypt(nonce, sealed, None).decode("utf-8")
    except Exception:
        logger.exception("Không giải mã được nội dung tin nhắn")
        return ""


def is_encrypted(stored: str | None) -> bool:
    return bool(stored) and stored.startswith(PREFIX)
