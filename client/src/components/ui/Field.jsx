import { useId } from 'react';
import cn from '../../services/utils/cn';

export const controlClass =
  'w-full rounded-lg bg-surface px-3 text-sm text-fg ring-1 ring-inset ring-line ' +
  'transition-shadow duration-150 placeholder:text-fg-subtle ' +
  'hover:ring-line-strong focus:ring-2 focus:ring-accent ' +
  'disabled:cursor-not-allowed disabled:bg-surface-2 disabled:text-fg-subtle';

/**
 * Bọc một ô nhập: nhãn, mô tả, thông báo lỗi.
 *
 * Tự sinh id và nối `aria-describedby` / `aria-invalid` vào ô con, nên thông
 * báo lỗi được trình đọc màn hình đọc lên chứ không chỉ là dòng chữ đỏ.
 */
function Field({ label, hint, error, required, className, children, htmlFor }) {
  const autoId = useId();
  const id = htmlFor || autoId;
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      {label && (
        <label htmlFor={id} className='text-sm font-medium text-fg'>
          {label}
          {required && (
            <span className='ml-0.5 text-danger-text' aria-hidden='true'>
              *
            </span>
          )}
        </label>
      )}
      {typeof children === 'function'
        ? children({
            id,
            'aria-describedby': cn(hintId, errorId) || undefined,
            'aria-invalid': error ? true : undefined,
          })
        : children}
      {hint && !error && (
        <p id={hintId} className='text-xs text-fg-subtle'>
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className='text-xs font-medium text-danger-text'>
          {error}
        </p>
      )}
    </div>
  );
}

export default Field;
