import cn from '../../services/utils/cn';

const TONES = {
  neutral: 'bg-surface-2 text-fg-muted ring-line',
  brand: 'bg-brand-soft text-brand-text ring-brand/20',
  accent: 'bg-accent-soft text-accent-text ring-accent/25',
  success: 'bg-success-soft text-success-text ring-success/25',
  warning: 'bg-warning-soft text-warning-text ring-warning/25',
  danger: 'bg-danger-soft text-danger-text ring-danger/25',
};

/**
 * Nhãn nhỏ: nguồn tin tuyển dụng, trình độ tiếng Nhật, kỹ năng, trạng thái.
 *
 * Mỗi sắc thái mang một nghĩa cố định trong toàn ứng dụng — xanh asagi là kỹ
 * năng, vàng yamabuki là kinh nghiệm, đỏ son là điều kiện bắt buộc chưa đạt.
 */
function Badge({ tone = 'neutral', icon: Icon, className, children, ...rest }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-pill px-2 py-0.5 text-2xs font-semibold ring-1 ring-inset',
        TONES[tone] ?? TONES.neutral,
        className
      )}
      {...rest}
    >
      {Icon && <Icon className='size-3 shrink-0' aria-hidden='true' />}
      {children}
    </span>
  );
}

export default Badge;
