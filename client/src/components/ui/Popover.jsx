import { useEffect, useRef } from 'react';
import cn from '../../services/utils/cn';

/**
 * Bảng thả xuống neo dưới một nút trên thanh trên cùng.
 *
 * Bản cũ của cả ba bảng (thông báo, tin nhắn, tìm người) dùng cùng một mẹo:
 * luôn render và chuyển `h-0` ↔ `h-[90vh]`. Hệ quả:
 *   - 90vh cao hơn phần màn hình còn lại dưới thanh trên cùng, nên đuôi bảng
 *     bị cắt và không cuộn tới được.
 *   - Lúc đóng, nội dung vẫn nằm trong cây DOM: trình đọc màn hình vẫn đọc,
 *     phím Tab vẫn đi vào.
 *   - Bấm ra ngoài không đóng được, phải bấm lại đúng cái nút vừa mở.
 *
 * Ở đây: đóng thì không render, mở thì cao tối đa vừa khung nhìn, bấm ra ngoài
 * hoặc bấm Esc là đóng.
 */
function Popover({ open, onClose, title, actions, footer, className, children }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const onPointerDown = (e) => {
      // Bỏ qua cú bấm trên chính nút mở: nút đó tự đảo trạng thái, xử lý cả
      // hai nơi thì bảng đóng rồi mở lại ngay trong cùng một cú bấm.
      if (ref.current && !ref.current.parentElement?.contains(e.target)) onClose?.();
    };
    const onKeyDown = (e) => e.key === 'Escape' && onClose?.();
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      ref={ref}
      className={cn(
        'absolute right-0 top-full z-40 mt-2 flex w-[min(22rem,calc(100vw-1.5rem))] animate-pop flex-col',
        'max-h-[min(32rem,calc(100vh-theme(spacing.header)-2rem))] overflow-hidden',
        'rounded-card bg-surface shadow-pop ring-1 ring-inset ring-line',
        className
      )}
    >
      {title && (
        <header className='flex shrink-0 items-center justify-between gap-3 border-b border-line px-4 py-3'>
          <h2 className='text-sm font-bold text-fg'>{title}</h2>
          {actions}
        </header>
      )}
      <div className='min-h-0 flex-1 overflow-y-auto overscroll-contain p-2'>
        {children}
      </div>
      {footer && (
        <footer className='shrink-0 border-t border-line p-2'>{footer}</footer>
      )}
    </div>
  );
}

export default Popover;
