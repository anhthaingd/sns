"""Gói Socket.IO: giữ tham chiếu tới instance dùng chung.

Controller và service cần emit sự kiện (ví dụ push thông báo khi ai đó like
bài viết) nhưng không nên import thẳng ``main.sio`` — sẽ tạo vòng import.
Module này là trung gian: ``main.py`` gọi ``set_sio()`` lúc khởi tạo, phần
còn lại import ``get_sio()`` khi cần emit.
"""

import socketio

_sio: socketio.AsyncServer | None = None


def set_sio(sio: socketio.AsyncServer) -> None:
    global _sio
    _sio = sio


def get_sio() -> socketio.AsyncServer | None:
    return _sio
