"""Parser cho từng trang nguồn.

Mỗi module chỉ làm đúng một việc: HTML -> `RawJob` với các trường còn ở dạng
văn bản thô. Việc chuẩn hoá (đổi lương ra yên/năm, quy trình độ ngôn ngữ về
một thang, trích kỹ năng) nằm chung ở `app/services/etl/extract.py`, không lặp
lại trong từng parser.
"""

from app.services.etl.parsers import daijob, gaijinpot, linkedin, nihongo
from app.services.etl.parsers.base import RawCompany, RawJob

# Mỗi nguồn: hàm dựng URL theo trang + hàm parse. `list_url` nhận số trang
# bắt đầu từ 1.
SOURCES = {
    "gaijinpot": {"list_url": gaijinpot.list_url, "parse": gaijinpot.parse_jobs},
    "daijob": {"list_url": daijob.list_url, "parse": daijob.parse_jobs},
    "nihongo": {"list_url": nihongo.list_url, "parse": nihongo.parse_jobs},
    "linkedin": {"list_url": linkedin.list_url, "parse": linkedin.parse_jobs},
}

__all__ = ["SOURCES", "RawCompany", "RawJob", "daijob", "gaijinpot", "linkedin", "nihongo"]
