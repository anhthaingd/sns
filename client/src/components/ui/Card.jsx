import cn from '../../services/utils/cn';

/**
 * Mặt phẳng chứa nội dung.
 *
 * Dùng `ring-1 ring-inset` thay cho `border`: viền trong không cộng thêm 1px
 * vào kích thước nên thẻ nằm trong lưới không bị lệch, và khi rê chuột đổi
 * sang màu asagi cũng không làm nội dung dịch đi.
 */
function Card({
  as: Tag = 'div',
  interactive = false,
  padded = true,
  className,
  children,
  ...rest
}) {
  return (
    <Tag
      className={cn(
        'rounded-card bg-surface ring-1 ring-inset ring-line',
        padded && 'p-4 sm:p-5',
        interactive &&
          'cursor-pointer transition-all duration-150 ease-out hover:shadow-card-hover hover:ring-accent/40',
        className
      )}
      {...rest}
    >
      {children}
    </Tag>
  );
}

export default Card;
