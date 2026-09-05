import aiofiles.os

from app.config.settings import BASE_DIR


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
            print(f"Refused to delete outside public/: {file_path}")
            return

        await aiofiles.os.remove(target)
        print(f"File deleted: {target}")
    except FileNotFoundError:
        print(f"File does not exist: {file_path}")
    except Exception as e:
        print(f"Error deleting file: {e}")
