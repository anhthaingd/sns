"""Chuẩn hoá dữ liệu tự do trong tin tuyển dụng thành trường có kiểu.

Toàn bộ hàm ở đây là **hàm thuần**: vào chuỗi, ra giá trị. Không chạm mạng,
không chạm DB — nên test được bằng bảng ca kiểm thử, không cần dựng gì.

Dữ liệu trộn hai ngôn ngữ và mỗi nguồn viết một kiểu, ví dụ cùng là mức lương:

    ¥250,000 ~ ¥300,000 / Month      (GaijinPot)
    ¥3.8M ~ ¥5.0M / Year             (GaijinPot)
    日本・円 350万円 〜 400万円        (DaiJob)
    月給25万円                        (tin tiếng Nhật khác)

Tất cả phải quy về **yên/năm** thì bộ lọc "lương tối thiểu" mới đúng — nếu để
lẫn lương tháng với lương năm thì kết quả lệch 12 lần.
"""

import re

from app.models.job import JLPT_TO_LEVEL

MONTHS_PER_YEAR = 12

# --- ngôn ngữ ---------------------------------------------------------------

# Xếp từ CỤ THỂ tới CHUNG CHUNG: "native" phải được thử trước "none" vì chuỗi
# "Native level" cũng chứa... (không chứa "none", nhưng nguyên tắc vẫn đúng cho
# "business conversation" vs "conversation").
_LANGUAGE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"母国語|ネイティブ|native", re.IGNORECASE), "native"),
    (re.compile(r"流暢|fluent|near[- ]native", re.IGNORECASE), "fluent"),
    (re.compile(r"ビジネス(?:会話)?|business", re.IGNORECASE), "business"),
    (re.compile(r"日常会話|conversation", re.IGNORECASE), "conversational"),
    (re.compile(r"初級|基礎|basic|beginner|elementary", re.IGNORECASE), "basic"),
    (re.compile(r"不問|不要|なし|\bnone\b|not required|no japanese", re.IGNORECASE), "none"),
]

_JLPT = re.compile(r"\bN\s?([1-5])\b", re.IGNORECASE)


def parse_language_level(text: str | None) -> str | None:
    """Quy mọi cách diễn đạt trình độ ngôn ngữ về một thang duy nhất.

    Thang: none < basic < conversational < business < fluent < native
    (xem `LANGUAGE_LEVELS` trong app/models/job.py).
    """
    if not text:
        return None
    cleaned = text.strip()
    if not cleaned:
        return None

    # JLPT ưu tiên hơn mô tả bằng lời: "N2 (ビジネスレベル)" thì N2 là thông tin
    # chính xác hơn.
    jlpt = _JLPT.search(cleaned)
    if jlpt:
        return JLPT_TO_LEVEL[f"N{jlpt.group(1)}"]

    for pattern, level in _LANGUAGE_PATTERNS:
        if pattern.search(cleaned):
            return level
    return None


# --- lương ------------------------------------------------------------------

_MAN_YEN = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*万")
_YEN_PLAIN = re.compile(r"[¥￥]?\s*(\d[\d,]{2,})")
_MILLION = re.compile(r"[¥￥]?\s*(\d+(?:\.\d+)?)\s*M\b", re.IGNORECASE)

_MONTHLY = re.compile(r"/\s*month|月給|月収|per month", re.IGNORECASE)
# Lương giờ / theo dự án / theo buổi: không có số giờ hay số buổi trong tin
# nên không quy đổi sang năm được. GaijinPot có thật: "¥5,000 ~ ¥15,000 / Project".
_NON_PERIODIC = re.compile(
    r"/\s*(?:hour|project|session|day|lesson|class)"
    r"|時給|日給"
    # "1,452 - 1,952 yen per 40-minute lesson" — số phút chen giữa nên không thể
    # liệt kê cứng từng cụm.
    r"|per\s+[\d\s-]*(?:minute|min|hour|lesson|class|session|day|project)",
    re.IGNORECASE,
)

# Tiền tệ khác yên. DaiJob có tin trả bằng Ringgit Malaysia: "7.8万リンギット"
# từng bị đọc thành 78.000 YÊN và lọt vào bộ lọc lương như một công việc cực rẻ.
_FOREIGN_CURRENCY = re.compile(
    r"リンギット|ドル|ユーロ|ウォン|人民元|ポンド|バーツ|ルピー"
    r"|\b(?:usd|eur|gbp|krw|cny|myr|sgd|thb|inr|aud)\b",
    re.IGNORECASE,
)
_JPY_MARKER = re.compile(r"[¥￥]|日本・円|円|\bjpy\b|\byen\b", re.IGNORECASE)

# Phần trong ngoặc CÓ CHỨA SỐ là diễn giải lại con số chính, không phải mức
# lương thứ hai. DaiJob có thật:
#   "日本・円 300万円 （Monthly Salary Range： 日本・円 25万円 *Divided into 12 month）"
# tức 3.000.000/năm, chia 12 tháng — nhưng 25万 bị đọc thành mức tối thiểu.
# Ngoặc KHÔNG chứa số thì giữ lại, vì đó thường là đơn vị ("(monthly)").
_NUMERIC_PARENTHETICAL = re.compile(r"[（(][^）)]*\d[^）)]*[）)]")

# Sau mốc chu kỳ ("/ Month") thường là phụ cấp, thưởng, trợ cấp đi lại — không
# phải lương. "¥200,000 ~ ¥240,000 / Month Transportation costs ... 30,000 yen
# per month" từng cho ra mức tối thiểu 360.000/năm.
_PERIOD_MARKER = re.compile(r"/\s*(?:month|year)|月給|月収|年収", re.IGNORECASE)

# Có dấu hiệu tiền tệ hay không quyết định ngưỡng an toàn cho số trần.
_CURRENCY_HINT = re.compile(r"[¥￥]|円|jpy|yen|salary|給|年収|月収", re.IGNORECASE)

# Không có dấu hiệu tiền tệ thì số phải đủ lớn mới coi là lương: tin của
# GaijinPot có chuỗi "Date August 21, 2026" ngay cạnh mức lương, và "2026" từng
# bị đọc thành lương 2.026 yên.
_MIN_BARE_NUMBER = 100_000


def _to_int(raw: str) -> int:
    return int(float(raw.replace(",", "")))


def parse_salary(text: str | None) -> tuple[int | None, int | None]:
    """Trả về (tối thiểu, tối đa) tính bằng YÊN/NĂM. Không đọc được thì (None, None)."""
    if not text:
        return None, None

    # Trả bằng ngoại tệ thì không quy đổi được (tỷ giá đổi hằng ngày) -> bỏ trống.
    if _FOREIGN_CURRENCY.search(text) and not _JPY_MARKER.search(text):
        return None, None

    text = _NUMERIC_PARENTHETICAL.sub(" ", text)

    # Chỉ đọc phần TRƯỚC mốc chu kỳ; phần sau là phụ cấp chứ không phải lương.
    # Chỉ áp dụng khi mốc đứng SAU con số ("¥240,000 / Month ..."). Tiếng Nhật
    # đặt mốc lên TRƯỚC ("月給25万円") — cắt ở đó thì mất luôn con số.
    period = _PERIOD_MARKER.search(text)
    if period and re.search(r"\d", text[: period.start()]):
        text = text[: period.end()]

    values: list[int] = []
    if _MAN_YEN.search(text):
        values = [_to_int(m) * 10_000 for m in _MAN_YEN.findall(text)]
    elif _MILLION.search(text):
        values = [int(float(m) * 1_000_000) for m in _MILLION.findall(text)]
    else:
        floor = 1000 if _CURRENCY_HINT.search(text) else _MIN_BARE_NUMBER
        values = [v for v in (_to_int(m) for m in _YEN_PLAIN.findall(text)) if v >= floor]

    if not values:
        return None, None

    if _NON_PERIODIC.search(text):
        return None, None

    if _MONTHLY.search(text):
        values = [v * MONTHS_PER_YEAR for v in values]

    values = sorted(set(values))
    return values[0], values[-1]


# --- số năm kinh nghiệm -----------------------------------------------------

_YEARS_PATTERNS = [
    re.compile(r"(\d+)\s*年以上"),
    re.compile(r"経験\s*(\d+)\s*年"),
    re.compile(r"(\d+)\s*\+?\s*years?", re.IGNORECASE),
    re.compile(r"at least\s*(\d+)\s*years?", re.IGNORECASE),
]
_NO_EXPERIENCE = re.compile(r"未経験|経験不問|no experience|entry[- ]level", re.IGNORECASE)


def parse_min_years(text: str | None) -> int | None:
    if not text:
        return None
    if _NO_EXPERIENCE.search(text):
        return 0
    for pattern in _YEARS_PATTERNS:
        found = pattern.findall(text)
        if found:
            # Tin hay nhắc nhiều mốc ("3年以上", "5年以上尚可") -> lấy mốc THẤP
            # nhất vì đó mới là điều kiện bắt buộc.
            return min(int(v) for v in found)
    return None


# --- hình thức làm việc -----------------------------------------------------

_EMPLOYMENT = [
    (re.compile(r"part[- ]time|アルバイト|パート", re.IGNORECASE), "part-time"),
    (re.compile(r"contract|契約社員|派遣", re.IGNORECASE), "contract"),
    (re.compile(r"intern", re.IGNORECASE), "internship"),
    (re.compile(r"freelance|業務委託", re.IGNORECASE), "freelance"),
    (re.compile(r"full[- ]time|正社員", re.IGNORECASE), "full-time"),
]
_REMOTE = re.compile(r"remote|リモート|在宅|テレワーク|work from home", re.IGNORECASE)


def parse_employment_type(text: str | None) -> str | None:
    if not text:
        return None
    for pattern, value in _EMPLOYMENT:
        if pattern.search(text):
            return value
    return None


def is_remote(text: str | None) -> bool:
    return bool(text and _REMOTE.search(text))


# --- địa điểm ---------------------------------------------------------------

# Chỉ liệt kê các tỉnh/thành thực sự xuất hiện trong tin tuyển dụng IT ở Nhật.
PREFECTURES = {
    "東京": "Tokyo",
    "大阪": "Osaka",
    "神奈川": "Kanagawa",
    "愛知": "Aichi",
    "京都": "Kyoto",
    "福岡": "Fukuoka",
    "北海道": "Hokkaido",
    "兵庫": "Hyogo",
    "埼玉": "Saitama",
    "千葉": "Chiba",
    "静岡": "Shizuoka",
    "広島": "Hiroshima",
    "宮城": "Miyagi",
    "沖縄": "Okinawa",
    "長野": "Nagano",
    "福井": "Fukui",
    "石川": "Ishikawa",
    "岡山": "Okayama",
    "熊本": "Kumamoto",
    "新潟": "Niigata",
    "香川": "Kagawa",
    "愛媛": "Ehime",
    "茨城": "Ibaraki",
    "栃木": "Tochigi",
    "群馬": "Gunma",
    "岐阜": "Gifu",
    "三重": "Mie",
    "滋賀": "Shiga",
    "奈良": "Nara",
    "和歌山": "Wakayama",
    "山口": "Yamaguchi",
    "長崎": "Nagasaki",
    "鹿児島": "Kagoshima",
    "青森": "Aomori",
    "岩手": "Iwate",
    "秋田": "Akita",
    "山形": "Yamagata",
    "福島": "Fukushima",
    "富山": "Toyama",
    "山梨": "Yamanashi",
    "鳥取": "Tottori",
    "島根": "Shimane",
    "徳島": "Tokushima",
    "高知": "Kochi",
    "佐賀": "Saga",
    "大分": "Oita",
    "宮崎": "Miyazaki",
}
_PREFECTURE_EN = {v.lower(): v for v in PREFECTURES.values()}


def parse_prefecture(text: str | None) -> str | None:
    """Tên tỉnh/thành viết bằng tiếng Anh, để lọc chung được cả hai loại nguồn."""
    if not text:
        return None
    for jp, en in PREFECTURES.items():
        if jp in text:
            return en
    lowered = text.lower()
    for en_lower, en in _PREFECTURE_EN.items():
        if re.search(rf"(?<![a-z]){re.escape(en_lower)}(?![a-z])", lowered):
            return en
    return None


# --- tên công ty ------------------------------------------------------------

_COMPANY_NOISE = re.compile(
    r"株式会社|有限会社|合同会社|合資会社|（株）|\(株\)|"
    r"\b(?:inc|corp|corporation|co|ltd|llc|k\.?k|kk|gmbh|pte|plc|limited)\b\.?",
    re.IGNORECASE,
)


def normalize_company_name(name: str | None) -> str:
    """Khoá để nhận ra cùng một công ty ở nhiều nguồn.

    Mercari, Inc. / MERCARI / Mercari Co., Ltd.  ->  "mercari"
    Không có bước này thì mỗi nguồn tạo một bản ghi công ty riêng và số liệu
    "công ty này có bao nhiêu vị trí" sẽ sai.

    Giới hạn đã biết: chỉ gộp được các biến thể CÙNG hệ chữ. "株式会社メルカリ"
    và "Mercari, Inc." vẫn ra hai khoá khác nhau vì cần chuyển tự katakana sang
    romaji mới gộp được. Chấp nhận: mỗi nguồn dùng nhất quán một hệ chữ, và khoá
    chính vẫn là (source, source_id).
    """
    if not name:
        return ""
    cleaned = _COMPANY_NOISE.sub(" ", name)
    cleaned = re.sub(r"[^\w぀-ヿ一-鿿]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip().lower()


# --- văn bản ----------------------------------------------------------------

# Nhãn trang trí lặp lại ở mọi tin, không mang thông tin phân biệt. Đo được:
# để nguyên thì điểm khớp của job đúng tụt từ 0.645 xuống 0.352.
_DECORATION = re.compile(
    r"(?:(?<=\s)|^)(?:NEW|HOT|Nationwide)(?=\s|$)"
    r"|直接採用|Watch video presentation"
    r"|★|▲|●|■|◆",
    re.IGNORECASE,
)


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    cleaned = _DECORATION.sub(" ", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def build_search_text(title: str, company: str, skills: list[str], description: str) -> str:
    """Text đưa vào embedding.

    Cố ý ĐẶT TIÊU ĐỀ VÀ KỸ NĂNG LÊN TRƯỚC và cắt bớt mô tả: thí nghiệm cho thấy
    text càng sạch và càng đúng trọng tâm thì xếp hạng càng chính xác
    (top-3 đúng ngành: 2/3 -> 3/3).
    """
    parts = [title.strip()]
    if company:
        parts.append(f"Company: {company.strip()}")
    if skills:
        parts.append("Skills: " + ", ".join(skills))
    body = clean_text(description)
    if body:
        parts.append(body[:800])
    return ". ".join(p for p in parts if p)
