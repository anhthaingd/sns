import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGUAGES } from '../../i18n/config';

/**
 * Chuyển ngôn ngữ giao diện.
 *
 * Cố ý là ba nút bấm thẳng chứ không phải dropdown: chỉ có ba ngôn ngữ, và
 * dropdown trong dự án này đi kèm `useClickOutside` — thêm một chỗ nữa dùng
 * hook đó là thêm một chỗ nữa có thể kẹt trạng thái mở.
 *
 * `i18next-browser-languagedetector` tự ghi lựa chọn vào localStorage
 * (`social_app_lang`), nên ở đây không phải lưu tay.
 *
 * @param variant 'header' cho thanh trên cùng, 'auth' cho trang đăng nhập/đăng ký
 */
function LanguageSwitcher({ variant = 'header' }) {
  const { t, i18n } = useTranslation('common');
  const active = i18n.resolvedLanguage;

  const base =
    variant === 'auth'
      ? 'bg-white/80 text-neutral-700'
      : 'bg-neutral-200 dark:bg-neutral-600';

  return (
    <div
      className={`flex items-center rounded-full overflow-hidden text-xs font-bold ${base}`}
      role='group'
      aria-label={t('language.switcherLabel')}
    >
      {SUPPORTED_LANGUAGES.map((lang) => (
        <button
          key={lang.code}
          type='button'
          lang={lang.code}
          title={lang.label}
          aria-pressed={active === lang.code}
          className={`px-2 py-2 transition-colors ${
            active === lang.code
              ? 'bg-violet-500 text-neutral-100'
              : 'hover:bg-neutral-300 dark:hover:bg-neutral-500'
          }`}
          onClick={() => i18n.changeLanguage(lang.code)}
        >
          {lang.short}
        </button>
      ))}
    </div>
  );
}

export default LanguageSwitcher;
