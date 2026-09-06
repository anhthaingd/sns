/**
 * Kiểm tra tính toàn vẹn của các file dịch.
 *
 * Ba lỗi dưới đây đều KHÔNG làm hỏng build và KHÔNG hiện ra khi thử ngôn ngữ
 * mặc định — chúng chỉ lộ ra khi có người đổi sang ngôn ngữ khác, thường là
 * lúc demo. Nên phải bắt bằng máy:
 *
 *   1. Thiếu khoá ở một ngôn ngữ  -> câu đó lặng lẽ hiện tiếng Nhật.
 *   2. Lệch tham số `{{...}}`     -> câu hiện ra thiếu số liệu, ví dụ
 *                                    "còn thiếu  năm" (mất `{{short}}`).
 *   3. Thiếu dạng số nhiều        -> tiếng Anh viết "Found 1 results".
 *   4. Gọi `t('khoá')` không tồn tại, hoặc gọi `t('ns:khoá')` mà quên khai báo
 *      `ns` trong `useTranslation` -> nút bấm hiện ra chuỗi `actions.search`.
 *
 * Chạy: npm run check:i18n
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', 'src', 'i18n', 'locales');
const REFERENCE = 'ja'; // ngôn ngữ gốc của dự án
const errors = [];

const languages = readdirSync(ROOT).filter((d) => !d.startsWith('.'));

/** Làm phẳng JSON lồng nhau thành { "a.b.c": "giá trị" }. */
const flatten = (obj, prefix = '', out = {}) => {
  for (const [key, value] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === 'object' && !Array.isArray(value)) flatten(value, path, out);
    else out[path] = value;
  }
  return out;
};

const params = (text) =>
  new Set([...String(text).matchAll(/\{\{\s*(\w+)/g)].map((m) => m[1]));

const load = (lng) => {
  const dir = join(ROOT, lng);
  const result = {};
  for (const file of readdirSync(dir).filter((f) => f.endsWith('.json'))) {
    const ns = file.replace(/\.json$/, '');
    result[ns] = flatten(JSON.parse(readFileSync(join(dir, file), 'utf8')));
  }
  return result;
};

const catalogs = Object.fromEntries(languages.map((l) => [l, load(l)]));
const reference = catalogs[REFERENCE];
if (!reference) {
  console.error(`Không có thư mục ngôn ngữ gốc "${REFERENCE}"`);
  process.exit(1);
}

// --- 1. Cùng tập namespace + cùng tập khoá ---------------------------------
// So sánh sau khi bỏ hậu tố số nhiều: tiếng Anh có `key_one`/`key_other`,
// tiếng Nhật chỉ có `key_other` — khác nhau ở đây là ĐÚNG, không phải lỗi.
const stripPlural = (key) => key.replace(/_(zero|one|two|few|many|other)$/, '');
const baseKeys = (nsMap) => new Set(Object.keys(nsMap).map(stripPlural));

for (const lng of languages) {
  const nsRef = Object.keys(reference).sort();
  const nsLng = Object.keys(catalogs[lng]).sort();
  for (const ns of nsRef) {
    if (!nsLng.includes(ns)) { errors.push(`[${lng}] thiếu namespace "${ns}"`); continue; }
    const want = baseKeys(reference[ns]);
    const have = baseKeys(catalogs[lng][ns]);
    for (const key of want) if (!have.has(key)) errors.push(`[${lng}] ${ns}: thiếu khoá "${key}"`);
    for (const key of have) if (!want.has(key)) errors.push(`[${lng}] ${ns}: dư khoá "${key}" (không có ở ${REFERENCE})`);
  }
  for (const ns of nsLng) if (!nsRef.includes(ns)) errors.push(`[${lng}] dư namespace "${ns}"`);
}

/**
 * Tham số CỐ Ý chỉ một ngôn ngữ dùng, dạng `namespace.khoá:tham_số`.
 *
 * Thêm vào đây phải kèm lý do. Danh sách càng ngắn càng tốt — mỗi dòng ở đây
 * là một chỗ máy không kiểm được nữa.
 */
const SINGLE_LANGUAGE_PARAMS = new Set([
  // Lương: ja/vi đọc theo 万 (`minMan`), en đọc theo triệu yên (`minM`).
  // `jobFormat.js` truyền sẵn cả hai bộ số cho mọi ngôn ngữ.
  'job.salary.range:minM',
  'job.salary.range:maxM',
  'job.salary.single:minM',
]);

// --- 2. Tham số phải nằm trong tập mà code truyền vào ------------------------
// KHÔNG đòi ba ngôn ngữ dùng y hệt một tập tham số: có câu cố ý khác nhau, ví
// dụ lương được viết `{{minMan}}万円` (ja/vi) nhưng `¥{{minM}}M` (en) vì hai
// nền văn hoá đọc số tiền theo đơn vị khác nhau — `jobFormat.js` truyền sẵn cả
// hai. Cái thật sự sai là một bản dịch gọi tham số mà KHÔNG bản nào khác biết
// tới: gần như chắc chắn là gõ nhầm tên, và chỗ đó sẽ hiện ra trống.
for (const [ns, entries] of Object.entries(reference)) {
  for (const key of Object.keys(entries)) {
    const base = stripPlural(key);
    for (const lng of languages) {
      for (const [k, v] of Object.entries(catalogs[lng][ns] ?? {})) {
        if (stripPlural(k) !== base) continue;
        for (const p of params(v)) {
          const usedElsewhere = languages.some((other) =>
            other !== lng &&
            Object.entries(catalogs[other][ns] ?? {}).some(
              ([ok, ov]) => stripPlural(ok) === base && params(ov).has(p)
            )
          );
          if (
            !usedElsewhere &&
            !SINGLE_LANGUAGE_PARAMS.has(`${ns}.${base}:${p}`) &&
            languages.length > 1
          ) {
            errors.push(`[${lng}] ${ns}.${k}: tham số {{${p}}} không ngôn ngữ nào khác dùng — gõ nhầm tên?`);
          }
        }
      }
    }
  }
}

// --- 3. Dùng {{count}} thì phải có dạng số nhiều ----------------------------
// i18next tra khoá `key_other` (và `key_one` với tiếng Anh) khi có `count`.
// Viết một bản duy nhất `key` là dựa vào cơ chế fallback — chạy được nhưng
// tiếng Anh sẽ ra "Found 1 results".
const PLURAL_FORMS = { ja: ['other'], vi: ['other'], en: ['one', 'other'] };
for (const lng of languages) {
  for (const [ns, entries] of Object.entries(catalogs[lng])) {
    for (const [key, value] of Object.entries(entries)) {
      if (!params(value).has('count')) continue;
      if (!/_(zero|one|two|few|many|other)$/.test(key)) {
        errors.push(`[${lng}] ${ns}.${key}: dùng {{count}} nhưng thiếu hậu tố số nhiều`);
        continue;
      }
      const base = stripPlural(key);
      for (const form of PLURAL_FORMS[lng] ?? ['other']) {
        if (entries[`${base}_${form}`] === undefined) {
          errors.push(`[${lng}] ${ns}.${base}: thiếu dạng "_${form}"`);
        }
      }
    }
  }
}

// --- 4. Mọi `t('khoá')` trong mã nguồn đều phải tồn tại -------------------
//
// Đây là loại lỗi mà ba phép kiểm trên KHÔNG thấy: ba file dịch khớp nhau hoàn
// hảo, nhưng component gọi một khoá không có ở đâu cả. i18next không báo lỗi —
// nó in thẳng khoá ra màn hình. Đã xảy ra thật với `common:actions.search`:
// ba cái nút hiện chữ "actions.search" mà build vẫn xanh.
const SRC = join(dirname(fileURLToPath(import.meta.url)), '..', 'src');

const sourceFiles = (dir, out = []) => {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      if (entry !== 'locales') sourceFiles(full, out);
    } else if (/\.jsx?$/.test(entry)) {
      out.push(full);
    }
  }
  return out;
};

const stripComments = (code) =>
  code.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');

const referenceBase = Object.fromEntries(
  Object.entries(reference).map(([ns, entries]) => [ns, new Set(Object.keys(entries).map(stripPlural))])
);

for (const file of sourceFiles(SRC)) {
  const code = stripComments(readFileSync(file, 'utf8'));
  const declaration = code.match(/useTranslation\(\s*(?:'([^']+)'|\[([^\]]*)\])/);
  const calls = [...code.matchAll(/\bt\(\s*'([^']+)'/g)].map((m) => m[1]);
  if (!calls.length) continue;

  const where = file.slice(file.indexOf('/src/') + 1);
  if (!declaration) {
    // Hàm nhận `t` làm tham số (jobFormat.js, matchText.js) thì không cần hook.
    if (!/\(\s*t\s*,/.test(code)) errors.push(`${where}: gọi t() nhưng không có useTranslation`);
    continue;
  }
  const declared = declaration[1]
    ? [declaration[1]]
    : declaration[2].split(',').map((x) => x.trim().replace(/^['"]|['"]$/g, '')).filter(Boolean);

  for (const call of calls) {
    const [ns, key] = call.includes(':') ? call.split(/:(.+)/) : [declared[0], call];
    if (!reference[ns]) {
      errors.push(`${where}: t('${call}') trỏ vào namespace không tồn tại "${ns}"`);
    } else if (!declared.includes(ns)) {
      errors.push(`${where}: t('${call}') nhưng useTranslation không khai báo "${ns}"`);
    } else if (reference[ns][key] === undefined && !referenceBase[ns].has(stripPlural(key))) {
      errors.push(`${where}: không có khoá "${ns}:${key}"`);
    }
  }
}

const unique = [...new Set(errors)];
const total = Object.values(reference).reduce((n, e) => n + Object.keys(e).length, 0);
if (unique.length) {
  console.error(`✗ ${unique.length} vấn đề trong file dịch:\n`);
  for (const e of unique) console.error('  ' + e);
  process.exit(1);
}
console.log(
  `✓ ${languages.length} ngôn ngữ (${languages.join(', ')}) · ` +
  `${Object.keys(reference).length} namespace · ${total} khoá — khớp nhau hoàn toàn`
);
