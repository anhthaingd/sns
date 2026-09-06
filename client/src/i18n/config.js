/**
 * Cấu hình đa ngôn ngữ.
 *
 * Ba lựa chọn ở đây đều có lý do, đừng đổi nếu chưa đọc `docs/09-da-ngon-ngu.md`:
 *
 * 1. Tài nguyên được **import tĩnh** (xem `resources.js`) chứ không tải qua
 *    HTTP. Ứng dụng phải demo được khi không có mạng, và tải động sẽ khiến
 *    trang loé lên khoá thô (`nav.search`) trước khi bản dịch về.
 * 2. Ngôn ngữ mặc định là **tiếng Nhật** — đây là sản phẩm cho thị trường Nhật.
 * 3. `fallbackLng` cũng là tiếng Nhật: thiếu khoá ở vi/en thì hiện tiếng Nhật,
 *    KHÔNG hiện khoá thô. Người dùng thấy chữ lạ còn hơn thấy `resume.save`.
 */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import resources from './resources';

export const DEFAULT_LANGUAGE = 'ja';

// Khoá localStorage đặt cùng khuôn với `social_app_theme` và `social_app_token`.
export const LANGUAGE_STORAGE_KEY = 'social_app_lang';

export const SUPPORTED_LANGUAGES = [
  { code: 'ja', label: '日本語', short: 'JA' },
  { code: 'vi', label: 'Tiếng Việt', short: 'VI' },
  { code: 'en', label: 'English', short: 'EN' },
];

export const SUPPORTED_CODES = SUPPORTED_LANGUAGES.map((l) => l.code);

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    supportedLngs: SUPPORTED_CODES,
    fallbackLng: DEFAULT_LANGUAGE,
    // Trình duyệt báo `ja-JP` / `vi-VN`; cắt phần vùng để khớp với `ja` / `vi`.
    load: 'languageOnly',
    // Không có namespace 'translation' mặc định — mọi khoá đều phải nói rõ mình
    // thuộc cụm nào, nếu không 10 namespace sẽ lẫn vào nhau.
    ns: Object.keys(resources[DEFAULT_LANGUAGE]),
    defaultNS: 'common',
    fallbackNS: 'common',
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: LANGUAGE_STORAGE_KEY,
      caches: ['localStorage'],
    },
    interpolation: {
      // React đã tự chống XSS khi render; để i18next escape nữa thì dấu nháy
      // trong tiếng Việt sẽ thành `&#39;`.
      escapeValue: false,
    },
    returnNull: false,
    // Bản dev kêu to khi thiếu khoá; bản production im lặng và dùng fallback.
    saveMissing: false,
    debug: false,
  });

export default i18n;

/**
 * Đồng bộ `<html lang>` với ngôn ngữ đang chọn.
 *
 * Không phải chuyện làm cho đẹp: trình duyệt dựa vào thuộc tính này để chọn
 * font và luật ngắt dòng cho chữ Nhật, còn trình đọc màn hình dựa vào nó để
 * chọn giọng đọc. Trang đang cứng `lang="en"` trong index.html thì tiếng Nhật
 * bị ngắt dòng sai chỗ.
 */
const syncDocumentLang = (lng) => {
  if (typeof document === 'undefined') return;
  document.documentElement.lang = lng;
};

syncDocumentLang(i18n.resolvedLanguage || DEFAULT_LANGUAGE);
i18n.on('languageChanged', syncDocumentLang);

/**
 * Ba bộ định dạng dùng trong câu dịch của phần gợi ý việc làm.
 *
 * Backend gửi về **dữ liệu thô** (`"business"`, `"japanese"`, `["Go","AWS"]`)
 * chứ không phải nhãn đã dịch — xem `app/services/matching.py`. Nhãn được ghép
 * ở đây, nên đổi ngôn ngữ là câu đổi theo mà không phải gọi lại API.
 */

// {{language, lang}} -> "日本語" / "Tiếng Nhật" / "Japanese"
i18n.services.formatter.add('lang', (value) =>
  i18n.t(`match:language.${value}`, { defaultValue: value })
);

// {{requiredLevel, level}} -> "ビジネス（N2）" ...
// Thang tiếng Nhật có kèm mã JLPT (N1-N5), thang tiếng Anh thì không — nên phải
// nhìn vào `language` của cùng câu đó để chọn đúng bảng nhãn.
i18n.services.formatter.add('level', (value, lng, options) => {
  const table = options?.language === 'english' ? 'englishLevel' : 'level';
  return i18n.t(`job:${table}.${value}`, { defaultValue: value });
});

// {{missing, list}} -> "Go、AWS" (ja) / "Go, AWS" (vi/en)
// Dùng Intl.ListFormat vì dấu ngăn cách khác nhau giữa các ngôn ngữ; nối bằng
// dấu phẩy cứng thì câu tiếng Nhật đọc sai quy ước.
i18n.services.formatter.add('list', (value, lng) => {
  if (!Array.isArray(value)) return String(value ?? '');
  try {
    return new Intl.ListFormat(lng, { style: 'narrow', type: 'unit' }).format(value);
  } catch {
    return value.join(', ');
  }
});
