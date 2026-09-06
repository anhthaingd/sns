"""Thống kê thị trường việc làm trên kho tin đã ETL.

Dùng cho hai việc: dựng màn hình "bản đồ thị trường", và cung cấp bức tranh nhu
cầu kỹ năng cho tầng mô phỏng đối chứng (`app/services/whatif.py`).

**Nguyên tắc trung thực của module này.** Đo trên chính dữ liệu dự án: nhóm tin
yêu cầu tiếng Nhật mức `none` chỉ có 12 tin ghi lương, mức `fluent` có 12 tin,
trong khi mức `business` có 101 tin. Một trung vị tính trên 12 mẫu mà hiển thị
ngang hàng với trung vị tính trên 101 mẫu là đánh lừa người đọc. Nên:

  * mọi trung vị đi kèm `salarySample`;
  * `salarySample < MIN_GROUP_SIZE` thì KHÔNG trả trung vị (trả `None`);
  * riêng kỹ năng, nhóm dưới ngưỡng được gộp vào một mục `__other__` thay vì
    liệt kê thành hàng chục dòng nhiễu.
"""

from app.models.job import LANGUAGE_LEVELS, Job

# Dưới ngưỡng này thì con số là giai thoại, không phải số liệu.
MIN_GROUP_SIZE = 10

# Trần số dòng trả về, để response không phình theo số kỹ năng trong từ điển.
SKILL_LIMIT = 30
PREFECTURE_LIMIT = 15

OTHER = "__other__"


def median(values: list[int | None]) -> int | None:
    known = sorted(v for v in values if v is not None)
    return known[len(known) // 2] if known else None


def _salary_fields(salaries: list[int | None]) -> dict:
    known = [s for s in salaries if s is not None]
    return {
        "salaryMedian": median(known) if len(known) >= MIN_GROUP_SIZE else None,
        "salarySample": len(known),
    }


async def _grouped(field: str, unwind: bool = False) -> list[dict]:
    pipeline: list[dict] = [{"$match": {"is_active": True}}]
    if unwind:
        pipeline.append({"$unwind": f"${field}"})
    pipeline += [
        {"$group": {"_id": f"${field}", "jobs": {"$sum": 1}, "salaries": {"$push": "$salary_min"}}},
        {"$sort": {"jobs": -1}},
    ]
    return await Job.aggregate(pipeline).to_list()


async def skill_demand(limit: int = SKILL_LIMIT) -> list[dict]:
    rows = await _grouped("required_skills", unwind=True)

    big = [r for r in rows if r["jobs"] >= MIN_GROUP_SIZE][:limit]
    small = [r for r in rows if r["jobs"] < MIN_GROUP_SIZE]

    result = [{"skill": r["_id"], "jobs": r["jobs"], **_salary_fields(r["salaries"])} for r in big]
    if small:
        result.append(
            {
                "skill": OTHER,
                "jobs": sum(r["jobs"] for r in small),
                "distinct": len(small),
                **_salary_fields([s for r in small for s in r["salaries"]]),
            }
        )
    return result


async def japanese_distribution() -> list[dict]:
    rows = {r["_id"]: r for r in await _grouped("required_japanese")}
    out = [
        {"level": level, "jobs": rows[level]["jobs"], **_salary_fields(rows[level]["salaries"])}
        for level in LANGUAGE_LEVELS
        if level in rows
    ]
    unstated = rows.get(None)
    if unstated:
        out.append({"level": None, "jobs": unstated["jobs"], **_salary_fields(unstated["salaries"])})
    return out


async def prefecture_distribution(limit: int = PREFECTURE_LIMIT) -> list[dict]:
    rows = await _grouped("prefecture")
    named = [r for r in rows if r["_id"]][:limit]
    return [{"prefecture": r["_id"], "jobs": r["jobs"], **_salary_fields(r["salaries"])} for r in named]


async def snapshot() -> dict:
    """Toàn bộ số liệu cho một lần vẽ màn hình."""
    return {
        "totalJobs": await Job.find({"is_active": True}).count(),
        "minGroupSize": MIN_GROUP_SIZE,
        "skills": await skill_demand(),
        "japanese": await japanese_distribution(),
        "prefectures": await prefecture_distribution(),
    }
