import { forwardRef } from 'react';
import cn from '../../services/utils/cn';

const VARIANTS = {
  soft: 'bg-surface-2 text-fg-muted hover:bg-surface-3 hover:text-fg',
  ghost: 'bg-transparent text-fg-muted hover:bg-surface-2 hover:text-fg',
  outline:
    'bg-surface text-fg-muted ring-1 ring-inset ring-line hover:bg-surface-2 hover:text-fg',
};

const SIZES = { sm: 'size-8 text-base', md: 'size-10 text-lg', lg: 'size-11 text-xl' };

/**
 * Nút chỉ có biểu tượng. `label` là bắt buộc — nó thành `aria-label` và
 * `title`, nếu không trình đọc màn hình chỉ đọc được "button".
 */
const IconButton = forwardRef(function IconButton(
  { variant = 'ghost', size = 'md', label, className, children, ...rest },
  ref
) {
  return (
    <button
      ref={ref}
      type='button'
      aria-label={label}
      title={label}
      className={cn(
        'inline-flex shrink-0 items-center justify-center rounded-full transition-all duration-150 ease-out',
        'active:scale-95 disabled:pointer-events-none disabled:opacity-50',
        VARIANTS[variant] ?? VARIANTS.ghost,
        SIZES[size] ?? SIZES.md,
        className
      )}
      {...rest}
    >
      {children}
    </button>
  );
});

export default IconButton;
