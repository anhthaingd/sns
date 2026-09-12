import { useCallback, useEffect, useRef } from 'react';
import { FaXmark } from 'react-icons/fa6';
import cn from '../../services/utils/cn';
import IconButton from './IconButton';

const WIDTHS = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-6xl',
};

/**
 * Khung hộp thoại dùng chung cho mọi modal.
 *
 * Gom về một chỗ những thứ mà từng modal trước đây tự làm mỗi nơi một kiểu —
 * và phần lớn là làm thiếu:
 *   - Bấm Esc để đóng.
 *   - Khoá cuộn trang nền (trước đây mở modal vẫn cuộn được trang dưới).
 *   - Bấm ra ngoài để đóng, nhưng bấm rồi kéo chuột ra ngoài thì KHÔNG đóng.
 *   - Trả con trỏ bàn phím về nút đã mở modal sau khi đóng.
 *   - `role="dialog"` + `aria-modal` + nối `aria-labelledby` vào tiêu đề.
 *
 * Phần thân tự cuộn khi dài, còn tiêu đề và chân luôn nhìn thấy.
 */
function Dialog({
  open,
  onClose,
  title,
  description,
  footer,
  size = 'md',
  closeOnBackdrop = true,
  busy = false,
  className,
  children,
}) {
  const panelRef = useRef(null);
  const pressedOnBackdrop = useRef(false);
  const restoreFocusTo = useRef(null);

  const close = useCallback(() => {
    if (!busy) onClose?.();
  }, [busy, onClose]);

  useEffect(() => {
    if (!open) return undefined;

    restoreFocusTo.current = document.activeElement;
    const { overflow } = document.body.style;
    document.body.style.overflow = 'hidden';

    const onKeyDown = (e) => {
      if (e.key === 'Escape') close();
    };
    document.addEventListener('keydown', onKeyDown);

    // Đưa con trỏ vào trong hộp thoại, nếu không phím Tab sẽ đi lạc ra trang nền.
    const focusTarget = panelRef.current?.querySelector(
      'input, textarea, select, button, [href], [tabindex]:not([tabindex="-1"])'
    );
    (focusTarget ?? panelRef.current)?.focus?.({ preventScroll: true });

    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = overflow;
      restoreFocusTo.current?.focus?.({ preventScroll: true });
    };
  }, [open, close]);

  if (!open) return null;

  const titleId = title ? 'fu-dialog-title' : undefined;

  return (
    <div
      className='fixed inset-0 z-[100] flex animate-fade-in items-end justify-center overflow-y-auto bg-ai-950/60 p-0 backdrop-blur-sm sm:items-center sm:p-4'
      onMouseDown={(e) => {
        pressedOnBackdrop.current = e.target === e.currentTarget;
      }}
      onMouseUp={(e) => {
        if (closeOnBackdrop && pressedOnBackdrop.current && e.target === e.currentTarget) {
          close();
        }
        pressedOnBackdrop.current = false;
      }}
    >
      <div
        ref={panelRef}
        role='dialog'
        aria-modal='true'
        aria-labelledby={titleId}
        aria-busy={busy || undefined}
        tabIndex={-1}
        className={cn(
          'relative flex max-h-[92vh] w-full animate-rise flex-col overflow-hidden bg-surface text-fg shadow-modal outline-none',
          'rounded-t-2xl sm:rounded-card',
          WIDTHS[size] ?? WIDTHS.md,
          className
        )}
      >
        {(title || onClose) && (
          <header className='flex shrink-0 items-start gap-4 border-b border-line px-5 py-4'>
            <div className='min-w-0 flex-1'>
              {title && (
                <h2 id={titleId} className='truncate text-base font-bold'>
                  {title}
                </h2>
              )}
              {description && (
                <p className='mt-0.5 text-sm text-fg-muted'>{description}</p>
              )}
            </div>
            {onClose && (
              <IconButton size='sm' label='Close' onClick={close} disabled={busy}>
                <FaXmark />
              </IconButton>
            )}
          </header>
        )}

        <div className='min-h-0 flex-1 overflow-y-auto px-5 py-4'>{children}</div>

        {footer && (
          <footer className='flex shrink-0 flex-wrap items-center justify-end gap-2 border-t border-line bg-surface-2/60 px-5 py-3'>
            {footer}
          </footer>
        )}
      </div>
    </div>
  );
}

export default Dialog;
