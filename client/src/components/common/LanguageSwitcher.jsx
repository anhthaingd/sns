import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGUAGES } from '../../i18n/config';
import cn from '../../services/utils/cn';

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

  return (
    <div
      className={cn(
        'inline-flex items-center gap-0.5 rounded-pill p-0.5 text-2xs font-bold',
        variant === 'auth' ? 'bg-white/15 backdrop-blur-sm' : 'bg-surface-2'
      )}
      role='group'
      aria-label={t('language.switcherLabel')}
    >
      {SUPPORTED_LANGUAGES.map((lang) => {
        const isActive = active === lang.code;
        return (
          <button
            key={lang.code}
            type='button'
            lang={lang.code}
            title={lang.label}
            aria-pressed={isActive}
            className={cn(
              'rounded-pill px-2.5 py-1 transition-colors duration-150',
              isActive
                ? 'bg-accent text-accent-on shadow-card'
                : variant === 'auth'
                  ? 'text-white/80 hover:bg-white/15 hover:text-white'
                  : 'text-fg-subtle hover:text-fg'
            )}
            onClick={() => i18n.changeLanguage(lang.code)}
          >
            {lang.short}
          </button>
        );
      })}
    </div>
  );
}

export default LanguageSwitcher;
