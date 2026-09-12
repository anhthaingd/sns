import cn from '../../services/utils/cn';

/**
 * Tiêu đề khu vực, có "dây chuông" — vạch dọc chuyển màu chàm → asagi nhắc
 * lại hình chiếc chuông gió trong tên Fuurin. Đây là dấu hiệu nhận diện lặp
 * lại ở tiêu đề trang và mục điều hướng đang mở.
 */
function SectionHeading({
  title,
  description,
  actions,
  level: Tag = 'h1',
  className,
}) {
  return (
    <div
      className={cn(
        'flex flex-wrap items-end justify-between gap-x-6 gap-y-3',
        className
      )}
    >
      <div className='relative min-w-0 pl-3.5'>
        <span className='fu-cord' aria-hidden='true' />
        <Tag className='truncate text-xl font-bold text-fg sm:text-2xl'>{title}</Tag>
        {description && (
          <p className='mt-1 text-sm text-fg-muted'>{description}</p>
        )}
      </div>
      {actions && <div className='flex shrink-0 items-center gap-2'>{actions}</div>}
    </div>
  );
}

export default SectionHeading;
