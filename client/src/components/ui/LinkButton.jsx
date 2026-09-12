import { Link } from 'react-router-dom';
import { buttonClass } from './buttonStyles';

/**
 * Liên kết trông như nút.
 *
 * Dùng khi thao tác là ĐI ĐẾN một trang khác: giữ được mở tab mới bằng
 * chuột giữa, sao chép địa chỉ, và trình đọc màn hình đọc là "liên kết" chứ
 * không phải "nút".
 *
 * `external` chuyển sang thẻ <a> thường cho địa chỉ ngoài ứng dụng.
 */
function LinkButton({
  to,
  href,
  external = false,
  variant = 'primary',
  size = 'md',
  icon: Icon,
  iconRight: IconRight,
  block,
  className,
  children,
  ...rest
}) {
  const classes = buttonClass({ variant, size, block, className });
  const content = (
    <>
      {Icon && <Icon className='size-4 shrink-0' aria-hidden='true' />}
      {children}
      {IconRight && <IconRight className='size-4 shrink-0' aria-hidden='true' />}
    </>
  );

  if (external || href) {
    return (
      <a
        className={classes}
        href={href || to}
        target='_blank'
        rel='noreferrer'
        {...rest}
      >
        {content}
      </a>
    );
  }

  return (
    <Link className={classes} to={to} {...rest}>
      {content}
    </Link>
  );
}

export default LinkButton;
