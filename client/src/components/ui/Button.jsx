import { forwardRef } from 'react';
import Spinner from './Spinner';
import { buttonClass } from './buttonStyles';

/**
 * Nút bấm dùng chung.
 *
 * `loading` giữ nguyên kích thước nút (con quay thay chỗ icon chứ không thay
 * chỗ chữ) để bố cục không nhảy khi bấm gửi.
 */
const Button = forwardRef(function Button(
  {
    variant = 'primary',
    size = 'md',
    icon: Icon,
    iconRight: IconRight,
    loading = false,
    block = false,
    className,
    children,
    disabled,
    type = 'button',
    ...rest
  },
  ref
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={buttonClass({ variant, size, block, className })}
      {...rest}
    >
      {loading ? (
        <Spinner className='size-4 shrink-0' />
      ) : (
        Icon && <Icon className='size-4 shrink-0' aria-hidden='true' />
      )}
      {children}
      {IconRight && !loading && (
        <IconRight className='size-4 shrink-0' aria-hidden='true' />
      )}
    </button>
  );
});

export default Button;
