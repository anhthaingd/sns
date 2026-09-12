import { FaInbox } from 'react-icons/fa6';
import EmptyState from './EmptyState';

/**
 * Giữ lại tên cũ để không phải sửa hàng chục nơi gọi cùng lúc; toàn bộ phần
 * hiển thị nay do `EmptyState` lo. Mã mới nên gọi thẳng `EmptyState` vì nó
 * nhận thêm mô tả và nút hành động.
 */
function NotFoundItem({ message, description, action }) {
  return (
    <EmptyState
      icon={FaInbox}
      title={message}
      description={description}
      action={action}
    />
  );
}

export default NotFoundItem;
