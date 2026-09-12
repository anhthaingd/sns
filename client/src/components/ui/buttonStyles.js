import cn from '../../services/utils/cn';

export const BUTTON_VARIANTS = {
  // Chàm đặc — hành động chính của mỗi màn hình. Mỗi màn chỉ nên có một cái.
  primary:
    'bg-brand text-brand-on hover:bg-brand-hover shadow-card disabled:hover:bg-brand',
  // Asagi đặc — hành động chính trong ngữ cảnh tuyển dụng (ứng tuyển, so khớp).
  accent:
    'bg-accent text-accent-on hover:bg-accent-hover shadow-card disabled:hover:bg-accent',
  // Viền — hành động phụ đứng cạnh hành động chính.
  outline:
    'bg-surface text-fg ring-1 ring-inset ring-line-strong hover:bg-surface-2',
  // Nền mờ — dùng trong thanh công cụ, nơi viền sẽ làm giao diện rối.
  soft: 'bg-surface-2 text-fg hover:bg-surface-3',
  // Trong suốt — hành động cấp ba, nút trong danh sách.
  ghost: 'bg-transparent text-fg-muted hover:bg-surface-2 hover:text-fg',
  // Đỏ son — chỉ cho thao tác xoá, không hoàn tác được.
  danger:
    'bg-danger text-white hover:bg-shu-600 shadow-card disabled:hover:bg-danger',
  dangerGhost: 'bg-transparent text-danger-text hover:bg-danger-soft',
  link: 'bg-transparent text-accent-text hover:underline underline-offset-4 px-0',
};

export const BUTTON_SIZES = {
  xs: 'h-7 px-2.5 text-2xs gap-1 rounded-md',
  sm: 'h-9 px-3 text-sm gap-1.5 rounded-lg',
  md: 'h-10 px-4 text-sm gap-2 rounded-lg',
  lg: 'h-12 px-6 text-base gap-2 rounded-xl',
};

/**
 * Class chung của nút.
 *
 * Tách khỏi component để <Link> của react-router mặc được đúng bộ áo — một
 * <button> bọc quanh <a> là HTML không hợp lệ và bàn phím không đi vào được.
 */
export function buttonClass({ variant = 'primary', size = 'md', block, className } = {}) {
  return cn(
    'inline-flex select-none items-center justify-center whitespace-nowrap font-semibold transition-all duration-150 ease-out',
    'active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50',
    BUTTON_VARIANTS[variant] ?? BUTTON_VARIANTS.primary,
    BUTTON_SIZES[size] ?? BUTTON_SIZES.md,
    block && 'w-full',
    className
  );
}
