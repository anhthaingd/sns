"""Sinh trang tài liệu HTML từ bộ ảnh mà `capture_docs.py` đã chụp.

Chạy TRÊN MÁY (không phải trong container), sau khi đã chụp ảnh:

    python3 e2e/build_doc_page.py                       # trang thường, ảnh để ngoài
    python3 e2e/build_doc_page.py --standalone          # MỘT file duy nhất, nhúng ảnh

Bản `--standalone` là bản để **gửi cho người ngoài**: mọi ảnh được nhúng thẳng
vào file dưới dạng data URI nên chỉ cần gửi đúng một file, người nhận bấm đúp là
mở bằng trình duyệt, không cần mạng nội bộ, không cần giải nén, không cần tài
khoản. Ảnh được giảm còn 256 màu trước khi nhúng — ảnh chụp giao diện toàn mảng
màu phẳng nên mắt thường không phân biệt được, mà dung lượng giảm khoảng 60%.
(Đã thử JPEG và WebP: JPEG còn NẶNG HƠN PNG với loại ảnh này, còn `sips` trên
macOS không xuất được WebP.)

Cần Pillow: `pip3 install pillow`.
"""

import argparse
import base64
import html
import io
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS_DIR = ROOT / "docs/screenshots"
MANIFEST = json.loads((SHOTS_DIR / "manifest.json").read_text(encoding="utf-8"))

parser = argparse.ArgumentParser(description="Sinh trang tai lieu giao dien")
parser.add_argument("--standalone", action="store_true", help="Nhung anh vao mot file duy nhat")
parser.add_argument("--out", help="Duong dan file ra")
args = parser.parse_args()

STANDALONE = args.standalone
OUT = pathlib.Path(
    args.out or (ROOT / ("Fuurin-so-tay-giao-dien.html" if STANDALONE else "docs/_build/so-tay-giao-dien.html"))
)
OUT.parent.mkdir(parents=True, exist_ok=True)


def image_src(filename):
    """Đường dẫn ảnh, hoặc data URI nếu đang đóng gói một file."""
    if not STANDALONE:
        return filename
    from PIL import Image

    im = Image.open(SHOTS_DIR / filename).convert("RGB")
    buf = io.BytesIO()
    im.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG).save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


GROUPS = [
    ("Xác thực", "auth", "Xác thực và lối vào", "Ba màn hình người dùng gặp trước khi có tài khoản."),
    (
        "Mạng xã hội",
        "social",
        "Mạng xã hội",
        "Bảng tin, channel, bài viết, bình luận, tìm kiếm, thông báo và nhắn tin.",
    ),
    (
        "Tuyển dụng",
        "jobs",
        "Tin tuyển dụng và CV",
        "Kho tin đã chuẩn hoá, và biểu mẫu CV làm đầu vào cho phần so khớp.",
    ),
    (
        "So khớp",
        "match",
        "So khớp và phân tích",
        "CV này hợp với ai, còn thiếu gì, bù chỗ nào lợi nhất, thị trường trả bao nhiêu.",
    ),
    (
        "Quản trị",
        "admin",
        "Trang quản trị",
        "Chỉ tài khoản có role.value = 1 vào được; người thường mở đúng đường dẫn cũng chỉ thấy trang 404.",
    ),
    (
        "Giao diện",
        "theme",
        "Chế độ tối và màn hình hẹp",
        "Cùng bộ mã nguồn, đổi theo thiết lập người dùng và bề ngang màn hình.",
    ),
]


def dims(path):
    out = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
        capture_output=True,
        text=True,
    ).stdout
    w = h = 0
    for line in out.splitlines():
        if "pixelWidth" in line:
            w = int(line.split(":")[1])
        elif "pixelHeight" in line:
            h = int(line.split(":")[1])
    return w, h


def esc(s):
    return html.escape(s, quote=True)


figures, toc = [], []
for group, slug, title, intro in GROUPS:
    shots = [s for s in MANIFEST if s["group"] == group]
    if not shots:
        continue
    toc.append(f'<a href="#{slug}"><span>{esc(title)}</span><em>{len(shots)}</em></a>')
    items = []
    for s in shots:
        w, h = dims(SHOTS_DIR / s["file"])
        tall = h / w > 0.75
        items.append(
            f'''      <figure class="shot{" shot--tall" if tall else ""}">
        <button class="shot__frame" type="button" data-title="{esc(s["title"])}">
          <img src="{image_src(s["file"])}" alt="{esc(s["title"])}" width="{w}" height="{h}" loading="lazy" decoding="async">
          <span class="shot__zoom">Phóng to</span>
        </button>
        <figcaption>
          <h3>{esc(s["title"])}</h3>
          <p>{esc(s["note"])}</p>
          <span class="shot__meta">{esc(s["file"])} · {w}×{h}</span>
        </figcaption>
      </figure>'''
        )
    figures.append(
        f'''    <section id="{slug}" class="group">
      <header class="group__head">
        <h2>{esc(title)}</h2>
        <p>{esc(intro)}</p>
      </header>
      <div class="grid">
{chr(10).join(items)}
      </div>
    </section>'''
    )

toc.append('<a href="#phat-hien"><span>Đã sửa</span><em>5</em></a>')

FINDINGS = [
    (
        "PUT /api/users/{id} xoá trắng trường không gửi kèm",
        "app/controllers/users.py · app/utils/forms.py",
        "<p><b>Triệu chứng.</b> Gọi endpoint chỉ để đổi ảnh đại diện là mất tên tài khoản. "
        "Gặp trực tiếp lúc dựng dữ liệu demo: sau khi tải ảnh lên, mọi bài viết mất tên tác giả.</p>"
        "<p><b>Nguyên nhân.</b> <code>update_user</code> dựng cả khối "
        '<code>{"username": username, "address": address, "intro": intro}</code> rồi '
        "<code>$set</code> một lần. Không đính <code>username</code> thì FastAPI đưa vào "
        "<code>None</code> và ghi đè. Chưa ai gặp vì <code>UpdateProfileModal.jsx</code> luôn gửi đủ "
        "ba trường — may mắn, không phải thiết kế.</p>"
        "<p><b>Bẫy khi sửa.</b> Cách hiển nhiên là <code>if value is not None</code>. Nhưng đo thử thì "
        "FastAPI đưa một field <i>gửi lên rỗng</i> (<code>intro=</code>) tới controller cũng dưới dạng "
        "<code>None</code> — không phân biệt được với field vắng mặt. Bản vá hiển nhiên kia đổi một lỗi "
        "mất dữ liệu lấy một lỗi mất chức năng: người dùng không xoá nổi phần giới thiệu của mình.</p>"
        '<p class="fix">Thêm <code>app/utils/forms.py</code> đọc thẳng tên field có trong form, rồi '
        "chỉ ghi những trường thật sự được gửi. Test canh hai đầu của cùng sự phân biệt đó: "
        "<code>test_partial_update_keeps_fields_that_were_not_sent</code> và "
        "<code>test_empty_string_still_clears_a_field</code>.</p>",
        "đã sửa",
    ),
    (
        "Ảnh đại diện thay bằng chữ cái đầu tên là code chết",
        "app/models/user.py · scripts/clear_default_avatars.py",
        "<p><b>Triệu chứng.</b> Trong mọi danh sách, mọi người là một vòng tròn xám giống hệt nhau.</p>"
        "<p><b>Nguyên nhân.</b> <code>Avatar.jsx</code> có sẵn phần dựng ảnh thay thế — chữ cái đầu của "
        "tên trên một trong sáu sắc chàm/asagi, chọn theo tên nên mỗi người một màu cố định. Nhưng model "
        "<code>User</code> khai báo <code>default_factory</code> trả về <code>avatar-trang.jpg</code>, "
        "nên mọi tài khoản mới đều <i>có</i> ảnh — cùng một file hình bóng người xám — và nhánh chữ cái "
        "đầu không bao giờ chạy.</p>"
        '<p class="fix">Bỏ mặc định (<code>avatar: dict | None = None</code>), kèm '
        "<code>scripts/clear_default_avatars.py</code> gỡ cho tài khoản cũ — chỉ đụng đúng file mặc định, "
        "ai đã tự tải ảnh lên thì giữ nguyên. Test canh: "
        "<code>test_new_account_has_no_default_avatar</code>.</p>",
        "đã sửa",
    ),
    (
        "Seed website mang logo cờ Mỹ và chữ Lorem ipsum",
        "server_python/data/social_app.webs.json",
        "<p><b>Triệu chứng.</b> Cài mới hệ thống ra một sản phẩm tuyển dụng thị trường Nhật treo cờ Mỹ, "
        "với hai câu giới thiệu bằng Lorem ipsum. Di sản từ template gốc.</p>"
        '<p class="fix">Bỏ hẳn trường <code>logo</code>: cả <code>Header.jsx</code> lẫn '
        "<code>AuthShell.jsx</code> đều đã có nhánh lùi về <code>/fuurin.svg</code> — ảnh phong linh của "
        "chính ứng dụng. Hai câu quote thay bằng câu thật, <code>color_title</code> về sắc chàm "
        "<code>#274A78</code>.</p>",
        "đã sửa",
    ),
    (
        "Bộ test API làm bẩn cơ sở dữ liệu phát triển",
        "server_python/tests/test_chat_web.py",
        "<p><b>Triệu chứng.</b> Ảnh chụp đầu tiên mang tiêu đề “Fuurin-bdd43”.</p>"
        "<p><b>Nguyên nhân.</b> Cấu hình website là bản ghi <i>dùng chung</i>, chỉ có đúng một bản trong "
        "DB. <code>test_admin_updates_website</code> đổi tên thành <code>Fuurin-&lt;hex&gt;</code> rồi "
        "bỏ đó.</p>"
        '<p class="fix">Test chụp lại nguyên trạng trước khi đổi và trả về trong <code>finally</code>. '
        "Kịch bản chụp ảnh cũng tự đặt lại cấu hình từ file seed, để một DB đã bẩn sẵn không kéo theo "
        "tài liệu.</p>",
        "đã sửa",
    ),
    (
        "Trang “thiếu sót của công ty” dài hơn 5.000 pixel",
        "app/controllers/match.py · components/GapList.jsx",
        "<p><b>Triệu chứng.</b> Với CV mẫu, <code>/match/companies/:id</code> của một công ty lớn liệt kê "
        "<strong>22 điều kiện bắt buộc và 54 điểm nên có</strong> — cuộn hơn năm màn hình, mỗi dòng là một "
        "khối chữ dài.</p>"
        "<p><b>Nguyên nhân.</b> Phần gộp cấp công ty loại trùng bằng cách so <i>nguyên câu</i> "
        "(<code>if gap.message not in seen</code>), mà <code>_check_skills</code> gói toàn bộ kỹ năng "
        "thiếu của một tin vào một mục. Hai tin khác nhau đúng một kỹ năng cho hai câu khác nhau, nên "
        "gần như không loại được gì.</p>"
        "<p><b>Cách sửa.</b> Viết lại <code>_combine_gaps</code> thành ba cách gộp cho ba loại câu hỏi: "
        "<b>ngôn ngữ và số năm</b> giữ mốc dễ nhất (“cửa thấp nhất vẫn cao hơn mình bao nhiêu”), "
        "<b>kỹ năng</b> bung ra từng cái rồi đếm số vị trí đang đòi nó và xếp giảm dần "
        "(“41/98 vị trí yêu cầu AWS”), <b>lương và địa điểm</b> loại trùng theo <code>code</code> + "
        "<code>params</code>. Thêm một quyết định: ở mức công ty kỹ năng không bao giờ mang nhãn “bắt "
        "buộc” — nhãn đó sinh ra ở mức từng tin, đưa lên mức công ty thì 75/91 dòng đều “bắt buộc”, tức "
        "không còn phân loại được gì.</p>"
        '<div class="table-scroll"><table><thead><tr><th></th><th>Trước</th><th>Sau</th></tr></thead>'
        "<tbody>"
        '<tr><td>Nhóm “bắt buộc phải bù”</td><td class="tnum">22 dòng</td>'
        '<td class="tnum"><strong>2 dòng</strong></td></tr>'
        '<tr><td>Nhóm “nên có thêm”</td><td class="tnum">54 dòng</td>'
        '<td class="tnum">83 dòng, xếp theo nhu cầu</td></tr>'
        '<tr><td>Dòng hiện ra khi mở trang</td><td class="tnum">76 khối chữ</td>'
        '<td class="tnum"><strong>14 dòng</strong></td></tr>'
        '<tr><td>Chiều cao trang</td><td class="tnum">&gt; 5.000 px</td>'
        '<td class="tnum">một màn hình rưỡi</td></tr>'
        "</tbody></table></div>"
        '<p class="fix">Kèm <code>GapList.jsx</code> chỉ hiện 12 mục đầu mỗi nhóm với nút “Xem thêm”. '
        "Test canh: năm test trong <code>tests/test_matching.py</code>.</p>",
        "đã sửa",
    ),
]

finding_html = "\n".join(
    f'''      <article class="finding" data-state="{esc(state)}">
        <header>
          <h3>{esc(title)}</h3>
          <span class="pill pill--{"done" if state == "đã sửa" else ("skip" if state == "đã né" else "open")}">{esc(state)}</span>
        </header>
        <p class="where"><code>{esc(where)}</code></p>
        {body}
      </article>'''
    for title, where, body, state in FINDINGS
)

TESTS = [
    ("login_page_loads_website_config_from_api", "Tên website lấy từ API chứ không viết cứng — backend + CORS sống"),
    ("unauthenticated_user_is_redirected_to_login", "Chưa đăng nhập thì không vào được trang trong"),
    ("register_then_login", "Đăng ký ghi vào DB, đăng nhập lấy được token"),
    ("wrong_password_shows_backend_error_message", "Sai mật khẩu hiện đúng câu chữ của backend, đã dịch"),
    ("plain_user_has_no_admin_menu", "Người thường không thấy menu quản trị"),
    ("admin_sees_admin_menu", "Quản trị viên thì thấy"),
    ("channel_join_and_post_flow", "Tạo channel → tham gia → đăng bài → bài hiện trên feed"),
    ("client_connects_to_socketio_and_receives_new_message", "Tin nhắn đẩy thời gian thực, huy hiệu chưa đọc hiện lên"),
    ("refresh_token_is_never_exposed_to_javascript", "Refresh token nằm trong cookie httpOnly"),
    ("recruitment_page_shows_structured_jobs_with_filters", "Bỏ một bộ lọc không làm mất bộ lọc còn lại"),
    ("match_page_requires_a_resume_then_shows_companies", "Chưa có CV thì chỉ đường tạo CV; có CV thì ra gợi ý"),
    ("whatif_recalculates_when_an_option_is_picked", "Tick một phương án thì con số kết hợp tính lại"),
    ("whatif_needs_a_resume_first", "Chưa có CV thì nói rõ, bằng câu chữ của backend"),
    ("market_page_shows_the_sample_size_next_to_every_median", "Không trung vị nào đứng một mình — luôn kèm cỡ mẫu"),
    ("switching_language_changes_the_whole_interface", "Đổi ngôn ngữ đổi cả chữ tĩnh lẫn câu backend sinh, nhớ qua F5"),
]
test_rows = "\n".join(
    f'        <tr><td class="tnum">{i}</td><td><code>{esc(name)}</code></td><td>{esc(what)}</td></tr>'
    for i, (name, what) in enumerate(TESTS, 1)
)

page = f"""<title>Sổ tay giao diện Fuurin</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Zen+Kaku+Gothic+New:wght@500;700;900&display=swap">
<style>
:root {{
  --washi: #F6F5F2;  --washi-2: #EFEDE8;
  --surface: #FFFFFF; --surface-2: #F4F3EF;
  --ink: #171C24;     --ink-2: #4A535F;   --ink-3: #7C8694;
  --line: #E1DFD8;    --line-2: #CFCCC3;
  --ai: #274A78;      --ai-soft: #E8EEF8;
  --asagi: #0A7070;   --asagi-soft: #E0F3F3;
  --shu: #A22F14;     --shu-soft: #FBEAE5;
  --matcha: #33653F;  --matcha-soft: #E7F0E8;
  --yamabuki: #7E591A;
  --shadow: 0 1px 2px rgb(23 28 36 / .05), 0 8px 24px -12px rgb(23 28 36 / .18);
  --shadow-lift: 0 2px 4px rgb(23 28 36 / .06), 0 18px 40px -16px rgb(23 28 36 / .28);
  color-scheme: light;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --washi: #0E1219;  --washi-2: #0A0D13;
    --surface: #161B24; --surface-2: #1D2430;
    --ink: #E8EAEE;     --ink-2: #A8B1BD;   --ink-3: #79838F;
    --line: #262E3A;    --line-2: #354050;
    --ai: #5C7DB3;      --ai-soft: #1B2740;
    --asagi: #21A3A3;   --asagi-soft: #06333A;
    --shu: #E0765A;     --shu-soft: #3A1810;
    --matcha: #7FAE86;  --matcha-soft: #14241A;
    --yamabuki: #C9A45C;
    --shadow: 0 1px 2px rgb(0 0 0 / .4), 0 8px 24px -12px rgb(0 0 0 / .6);
    --shadow-lift: 0 2px 4px rgb(0 0 0 / .5), 0 18px 40px -16px rgb(0 0 0 / .7);
    color-scheme: dark;
  }}
}}
:root[data-theme="dark"] {{
  --washi: #0E1219;  --washi-2: #0A0D13;
  --surface: #161B24; --surface-2: #1D2430;
  --ink: #E8EAEE;     --ink-2: #A8B1BD;   --ink-3: #79838F;
  --line: #262E3A;    --line-2: #354050;
  --ai: #5C7DB3;      --ai-soft: #1B2740;
  --asagi: #21A3A3;   --asagi-soft: #06333A;
  --shu: #E0765A;     --shu-soft: #3A1810;
  --matcha: #7FAE86;  --matcha-soft: #14241A;
  --yamabuki: #C9A45C;
  --shadow: 0 1px 2px rgb(0 0 0 / .4), 0 8px 24px -12px rgb(0 0 0 / .6);
  --shadow-lift: 0 2px 4px rgb(0 0 0 / .5), 0 18px 40px -16px rgb(0 0 0 / .7);
  color-scheme: dark;
}}

* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--washi);
  color: var(--ink);
  font: 400 16px/1.65 Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased;
}}
h1, h2, h3 {{
  font-family: "Zen Kaku Gothic New", Inter, ui-sans-serif, system-ui, sans-serif;
  text-wrap: balance;
  margin: 0;
}}
code {{
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;
  font-size: .875em;
  background: var(--surface-2);
  border-radius: 4px;
  padding: .1em .35em;
}}
a {{ color: var(--asagi); }}
.tnum {{ font-variant-numeric: tabular-nums; }}
:focus-visible {{ outline: 2px solid var(--asagi); outline-offset: 2px; border-radius: 4px; }}

/* --- Dải đầu trang, hoa văn seigaiha 青海波 ------------------------------ */
.masthead {{
  position: relative;
  overflow: hidden;
  background: linear-gradient(115deg, #1E3A60 0%, #274A78 45%, #0A7070 100%);
  color: #fff;
  padding: clamp(2.5rem, 6vw, 4.5rem) 0 clamp(2rem, 4vw, 3rem);
}}
.masthead::before {{
  content: "";
  position: absolute; inset: 0;
  background-image:
    radial-gradient(circle at 50% 100%, transparent 58%, rgb(255 255 255 / .10) 58.5%, rgb(255 255 255 / .10) 62%, transparent 62.5%),
    radial-gradient(circle at 50% 100%, transparent 38%, rgb(255 255 255 / .08) 38.5%, rgb(255 255 255 / .08) 42%, transparent 42.5%),
    radial-gradient(circle at 50% 100%, transparent 18%, rgb(255 255 255 / .06) 18.5%, rgb(255 255 255 / .06) 22%, transparent 22.5%);
  background-size: 72px 36px;
  background-position: 0 0, 0 0, 0 0;
  opacity: .85;
  pointer-events: none;
}}
.wrap {{ width: min(1180px, 100% - 3rem); margin-inline: auto; }}
.masthead .wrap {{ position: relative; }}
.eyebrow {{
  font-size: .75rem; font-weight: 600; letter-spacing: .14em; text-transform: uppercase;
  color: rgb(255 255 255 / .72); margin: 0 0 .75rem;
}}
.masthead h1 {{ font-size: clamp(2rem, 5vw, 3.25rem); font-weight: 900; letter-spacing: -.02em; line-height: 1.1; }}
.masthead .lede {{
  max-width: 58ch; margin: 1rem 0 0; color: rgb(255 255 255 / .82); font-size: 1.0625rem;
}}
.stats {{ display: flex; flex-wrap: wrap; gap: .625rem; margin-top: 1.75rem; }}
.stat {{
  display: flex; align-items: baseline; gap: .5rem;
  background: rgb(255 255 255 / .12);
  border: 1px solid rgb(255 255 255 / .18);
  border-radius: 999px; padding: .4rem .9rem;
  font-size: .875rem; color: rgb(255 255 255 / .9);
  backdrop-filter: blur(2px);
}}
.stat b {{ font-variant-numeric: tabular-nums; font-weight: 700; color: #fff; }}

/* --- Bố cục: cột mục lục dính + cột nội dung --------------------------- */
.shell {{ display: grid; grid-template-columns: 1fr; gap: 2.5rem; padding: 2.5rem 0 5rem; }}
@media (min-width: 1024px) {{
  .shell {{ grid-template-columns: 15rem 1fr; gap: 3.5rem; align-items: start; }}
  .toc {{ position: sticky; top: 1.5rem; }}
}}
.toc h2 {{
  font-size: .75rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
  color: var(--ink-3); margin-bottom: .75rem;
}}
.toc a {{
  display: flex; justify-content: space-between; align-items: center; gap: .75rem;
  padding: .5rem .75rem; border-radius: 8px; text-decoration: none;
  color: var(--ink-2); font-size: .9375rem; font-weight: 500;
}}
.toc a:hover {{ background: var(--surface-2); color: var(--ink); }}
.toc a[aria-current="true"] {{ background: var(--ai-soft); color: var(--ai); font-weight: 600; }}
.toc em {{ font-style: normal; font-variant-numeric: tabular-nums; font-size: .8125rem; color: var(--ink-3); }}

main {{ min-width: 0; display: flex; flex-direction: column; gap: 4rem; }}

.group__head {{ margin-bottom: 1.75rem; }}
.group__head h2 {{
  position: relative; padding-left: 1rem;
  font-size: clamp(1.375rem, 2.5vw, 1.75rem); font-weight: 700; letter-spacing: -.01em;
}}
/* Dây treo phong linh: cùng chi tiết dùng cho tiêu đề mục trong ứng dụng. */
.group__head h2::before {{
  content: ""; position: absolute; left: 0; top: .18em; bottom: .18em; width: 4px;
  border-radius: 999px; background: linear-gradient(to bottom, var(--ai), var(--asagi));
}}
.group__head p {{ margin: .625rem 0 0 1rem; color: var(--ink-2); max-width: 62ch; }}

.grid {{ display: grid; grid-template-columns: 1fr; gap: 1.5rem; }}
@media (min-width: 900px) {{ .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}

.shot {{
  margin: 0; display: flex; flex-direction: column;
  background: var(--surface); border-radius: 14px;
  box-shadow: var(--shadow);
  outline: 1px solid var(--line); outline-offset: -1px;
  overflow: hidden; transition: box-shadow .18s ease, transform .18s ease;
}}
.shot:hover {{ box-shadow: var(--shadow-lift); transform: translateY(-2px); }}
.shot__frame {{
  position: relative; display: block; width: 100%; padding: 0; border: 0; margin: 0;
  background: var(--surface-2); cursor: zoom-in; line-height: 0;
  border-bottom: 1px solid var(--line);
}}
.shot__frame img {{ display: block; width: 100%; height: auto; }}
.shot--tall .shot__frame img {{ height: 320px; object-fit: cover; object-position: top; }}
.shot--tall .shot__frame::after {{
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 64px;
  background: linear-gradient(to bottom, transparent, var(--surface));
  pointer-events: none;
}}
.shot__zoom {{
  position: absolute; right: .625rem; bottom: .625rem; z-index: 1;
  font: 600 .75rem/1 Inter, sans-serif; letter-spacing: .02em;
  background: rgb(23 28 36 / .78); color: #fff;
  padding: .375rem .625rem; border-radius: 999px;
  opacity: 0; transition: opacity .18s ease;
}}
.shot__frame:hover .shot__zoom, .shot__frame:focus-visible .shot__zoom {{ opacity: 1; }}
figcaption {{ padding: 1rem 1.125rem 1.125rem; display: flex; flex-direction: column; gap: .375rem; }}
figcaption h3 {{ font-size: 1rem; font-weight: 700; }}
figcaption p {{ margin: 0; font-size: .9375rem; color: var(--ink-2); }}
.shot__meta {{
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: .6875rem; color: var(--ink-3); font-variant-numeric: tabular-nums;
}}

/* --- Bảng test -------------------------------------------------------- */
.panel {{
  background: var(--surface); border-radius: 14px; padding: 1.5rem;
  outline: 1px solid var(--line); outline-offset: -1px; box-shadow: var(--shadow);
}}
.table-scroll {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: .9375rem; }}
th, td {{ text-align: left; padding: .625rem .75rem; border-bottom: 1px solid var(--line); vertical-align: top; }}
th {{
  font-size: .6875rem; letter-spacing: .1em; text-transform: uppercase;
  color: var(--ink-3); font-weight: 600; white-space: nowrap;
}}
tbody tr:last-child td {{ border-bottom: 0; }}
td.tnum {{ color: var(--ink-3); width: 2.5rem; }}
td code {{ white-space: nowrap; }}

/* --- Phát hiện -------------------------------------------------------- */
.findings {{ display: flex; flex-direction: column; gap: 1rem; }}
.finding {{
  background: var(--surface); border-radius: 14px; padding: 1.25rem 1.375rem;
  outline: 1px solid var(--line); outline-offset: -1px;
  border-left: 4px solid var(--line-2);
}}
.finding[data-state="chưa sửa"] {{ border-left-color: var(--shu); }}
.finding[data-state="đã sửa"] {{ border-left-color: var(--matcha); }}
.finding[data-state="đã né"] {{ border-left-color: var(--yamabuki); }}
.finding header {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }}
.finding h3 {{ font-size: 1.0625rem; font-weight: 700; }}
.finding p {{ margin: .625rem 0 0; color: var(--ink-2); font-size: .9375rem; max-width: 72ch; }}
.finding .where {{ margin-top: .375rem; }}
.finding .where code {{ background: none; padding: 0; color: var(--ink-3); font-size: .8125rem; }}
.finding .fix {{ color: var(--ink); }}
.pill {{
  flex: none; font-size: .75rem; font-weight: 600; padding: .25rem .625rem; border-radius: 999px;
  white-space: nowrap;
}}
.pill--open {{ background: var(--shu-soft); color: var(--shu); }}
.pill--done {{ background: var(--matcha-soft); color: var(--matcha); }}
.pill--skip {{ background: var(--surface-2); color: var(--yamabuki); }}

.note {{
  background: var(--asagi-soft); border-radius: 12px; padding: 1rem 1.25rem;
  font-size: .9375rem; color: var(--ink-2); border-left: 4px solid var(--asagi);
}}
.note strong {{ color: var(--ink); }}

pre.cmd {{
  margin: 1rem 0 0; padding: 1rem 1.125rem; border-radius: 12px; overflow-x: auto;
  background: var(--surface-2); outline: 1px solid var(--line); outline-offset: -1px;
  font: 400 .8125rem/1.7 ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--ink-2);
}}
pre.cmd .c {{ color: var(--ink-3); }}

footer {{
  border-top: 1px solid var(--line); padding: 2rem 0 3rem; margin-top: 1rem;
  color: var(--ink-3); font-size: .875rem;
}}

/* --- Lớp phủ xem ảnh đầy đủ ------------------------------------------- */
.lightbox {{
  position: fixed; inset: 0; z-index: 50; display: none;
  background: rgb(10 13 19 / .88); padding: 2rem 1rem;
  overflow: auto; -webkit-overflow-scrolling: touch;
}}
.lightbox[open] {{ display: block; }}
.lightbox img {{ display: block; width: min(1440px, 100%); margin: 0 auto; border-radius: 10px; }}
.lightbox__bar {{
  position: sticky; top: 0; display: flex; justify-content: space-between; align-items: center;
  gap: 1rem; width: min(1440px, 100%); margin: 0 auto .75rem;
  color: rgb(255 255 255 / .9); font-size: .875rem; font-weight: 600;
}}
.lightbox__close {{
  border: 1px solid rgb(255 255 255 / .3); background: rgb(255 255 255 / .1); color: #fff;
  border-radius: 999px; padding: .375rem .875rem; font: 600 .8125rem Inter, sans-serif; cursor: pointer;
}}
.lightbox__close:hover {{ background: rgb(255 255 255 / .2); }}

@media (prefers-reduced-motion: reduce) {{
  * {{ transition: none !important; }}
  .shot:hover {{ transform: none; }}
}}
</style>

<header class="masthead">
  <div class="wrap">
    <p class="eyebrow">Fuurin 風鈴 · Tài liệu giao diện</p>
    <h1>Sổ tay giao diện</h1>
    <p class="lede">
      Toàn bộ {len(MANIFEST)} màn hình của nền tảng tuyển dụng kiêm mạng xã hội Fuurin, chụp tự động
      bằng Playwright trên dữ liệu thật — không phải ảnh dựng tay.
    </p>
    <div class="stats">
      <span class="stat"><b>{len(MANIFEST)}</b> ảnh</span>
      <span class="stat"><b>20</b> đường dẫn</span>
      <span class="stat"><b>345</b> test API chạy qua</span>
      <span class="stat"><b>15</b> test giao diện chạy qua</span>
      <span class="stat"><b>3</b> ngôn ngữ · 572 khoá</span>
    </div>
  </div>
</header>

<div class="wrap shell">
  <nav class="toc" aria-label="Mục lục">
    <h2>Nội dung</h2>
    <a href="#kiem-thu"><span>Kiểm thử</span><em>360</em></a>
    {chr(10).join("    " + t for t in toc)}
  </nav>

  <main>
    <section id="kiem-thu" class="group">
      <header class="group__head">
        <h2>Kiểm thử tự động</h2>
        <p>
          Ảnh chụp chỉ chứng minh màn hình vẽ ra được. Chuyện màn hình làm đúng việc do hai bộ test
          dưới đây trả lời — cả hai chạy xanh ngay trước khi bộ ảnh này được tạo.
        </p>
      </header>
      <div class="panel">
        <div class="table-scroll">
          <table>
            <thead>
              <tr><th>#</th><th>Test giao diện (Playwright)</th><th>Kiểm điều gì</th></tr>
            </thead>
            <tbody>
{test_rows}
            </tbody>
          </table>
        </div>
      </div>
      <p class="note" style="margin-top:1rem">
        <strong>351 test API</strong> chạy riêng bằng pytest gọi thẳng vào FastAPI: 345 chạy qua,
        6 bỏ qua — chín test trong đó là mới, viết cùng lúc với năm bản vá bên dưới. Sáu test bỏ qua là nhóm thu thập tin tuyển dụng từ trang ngoài — chỉ chạy khi đặt
        <code>RUN_CRAWL_TESTS=1</code> vì phụ thuộc mạng và cấu trúc trang nguồn.
      </p>
      <pre class="cmd"><span class="c"># Dựng hệ thống rồi chụp lại toàn bộ (khoảng 6 phút)</span>
docker compose up -d
docker compose -f docker-compose.yml -f docker-compose.test.yml \\
    run --rm -e E2E_LANG=vi e2e-tests python -m e2e.capture_docs</pre>
    </section>

{chr(10).join(figures)}

    <section id="phat-hien" class="group">
      <header class="group__head">
        <h2>Năm lỗi tìm ra khi làm tài liệu — đã sửa</h2>
        <p>
          Đi hết mọi màn hình bằng dữ liệu thật làm lộ ra năm thứ bộ test không bắt được — vì test kiểm
          hành vi, không kiểm nội dung trông ra sao. Cả năm đều đã vá, mỗi bản vá kèm test canh cho nó
          không quay lại.
        </p>
      </header>
      <div class="findings">
{finding_html}
      </div>
    </section>
  </main>
</div>

<footer class="wrap">
  Sinh bởi <code>e2e/capture_docs.py</code> · ảnh gốc ở <code>docs/screenshots/</code> ·
  bản Markdown ở <code>docs/11-so-tay-giao-dien.md</code>
</footer>

<div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Ảnh đầy đủ">
  <div class="lightbox__bar">
    <span id="lightbox-title"></span>
    <button class="lightbox__close" type="button" id="lightbox-close">Đóng (Esc)</button>
  </div>
  <img id="lightbox-img" src="" alt="">
</div>

<script>
(function () {{
  var box = document.getElementById('lightbox');
  var img = document.getElementById('lightbox-img');
  var cap = document.getElementById('lightbox-title');
  var last = null;

  function open(src, title) {{
    img.src = src; img.alt = title; cap.textContent = title;
    box.setAttribute('open', ''); box.scrollTop = 0;
    document.body.style.overflow = 'hidden';
  }}
  function close() {{
    box.removeAttribute('open'); img.src = '';
    document.body.style.overflow = '';
    if (last) last.focus();
  }}

  document.querySelectorAll('.shot__frame').forEach(function (btn) {{
    btn.addEventListener('click', function () {{
      last = btn;
      open(btn.querySelector('img').src, btn.dataset.title);
    }});
  }});
  document.getElementById('lightbox-close').addEventListener('click', close);
  box.addEventListener('click', function (e) {{ if (e.target === box || e.target === img) close(); }});
  document.addEventListener('keydown', function (e) {{
    if (e.key === 'Escape' && box.hasAttribute('open')) close();
  }});

  // Đánh dấu mục đang đọc trong mục lục.
  var links = {{}};
  document.querySelectorAll('.toc a').forEach(function (a) {{ links[a.getAttribute('href').slice(1)] = a; }});
  var spy = new IntersectionObserver(function (entries) {{
    entries.forEach(function (en) {{
      var a = links[en.target.id];
      if (a && en.isIntersecting) {{
        Object.keys(links).forEach(function (k) {{ links[k].removeAttribute('aria-current'); }});
        a.setAttribute('aria-current', 'true');
      }}
    }});
  }}, {{ rootMargin: '-10% 0px -75% 0px' }});
  document.querySelectorAll('main section[id]').forEach(function (s) {{ spy.observe(s); }});
}})();
</script>
"""

# Bản artifact được máy chủ bọc sẵn <!doctype>/<head>; file rời thì phải tự bọc,
# nếu không trình duyệt đoán nhầm bảng mã và tiếng Việt hiện ra thành "Sá»• tay".
if STANDALONE:
    # Phần đầu của template (title, link font, style) thuộc về <head>; phần còn
    # lại từ dải masthead trở đi là <body>.
    marker = '<header class="masthead">'
    split = page.index(marker)
    head, body = page[:split].rstrip(), page[split:]
    page = (
        '<!doctype html>\n<html lang="vi">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"{head}\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )

OUT.write_text(page, encoding="utf-8")
size = OUT.stat().st_size
print(f"đã sinh {OUT}")
print(f"  {len(MANIFEST)} ảnh · {size / 1_048_576:.1f} MB" + ("  (một file, nhúng sẵn ảnh)" if STANDALONE else ""))
