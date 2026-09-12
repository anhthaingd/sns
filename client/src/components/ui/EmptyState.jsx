import cn from '../../services/utils/cn';

/**
 * Trạng thái rỗng.
 *
 * Bản cũ (`NotFoundItem`) chỉ in một dòng chữ in đậm giữa khung, không nói
 * người dùng nên làm gì tiếp. Ở đây có chỗ cho biểu tượng, câu gợi ý và một
 * nút hành động; nền là hoa văn sóng seigaiha rất mờ để ô trống không bị
 * nhầm với vùng đang tải.
 */
function EmptyState({ icon: Icon, title, description, action, className }) {
  return (
    <section
      className={cn(
        'relative overflow-hidden rounded-card bg-surface px-6 py-14 text-center ring-1 ring-inset ring-line',
        className
      )}
    >
      <div
        className='fu-seigaiha pointer-events-none absolute inset-0 text-fg opacity-[0.045]'
        aria-hidden='true'
      />
      <div className='relative flex flex-col items-center gap-3'>
        {Icon && (
          <span className='flex size-12 items-center justify-center rounded-full bg-accent-soft text-xl text-accent-text'>
            <Icon aria-hidden='true' />
          </span>
        )}
        <h3 className='text-base font-bold text-fg'>{title}</h3>
        {description && (
          <p className='max-w-sm text-sm leading-relaxed text-fg-muted'>
            {description}
          </p>
        )}
        {action && <div className='mt-1'>{action}</div>}
      </div>
    </section>
  );
}

export default EmptyState;
