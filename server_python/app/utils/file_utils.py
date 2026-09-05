import logging

import aiofiles.os

from app.config.settings import BASE_DIR

logger = logging.getLogger("fuurin.files")


async def delete_file(file_path: str):
    """Xoá file upload. `file_path` là đường dẫn tương đối lưu trong DB (vd: public/uploads/abc.png)."""
    if not file_path:
        return
    try:
        # Chuẩn hoá cả đường dẫn kiểu Windows còn sót trong dữ liệu cũ.
        relative = file_path.replace("\\", "/").lstrip("/")
        target = (BASE_DIR / relative).resolve()

        # Không cho xoá ra ngoài thư mục public/.
        if not target.is_relative_to((BASE_DIR / "public").resolve()):
            logger.warning("Từ chối xoá file ngoài public/: %s", file_path)
            return

        await aiofiles.os.remove(target)
        logger.info("Đã xoá file: %s", target)
    except FileNotFoundError:
        logger.info("File không tồn tại, bỏ qua: %s", file_path)
    except OSError:
        logger.exception("Lỗi khi xoá file %s", file_path)
