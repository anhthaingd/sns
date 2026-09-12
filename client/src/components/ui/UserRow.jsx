import { useNavigate } from 'react-router-dom';
import cn from '../../services/utils/cn';
import Avatar from './Avatar';

/**
 * Một dòng "người dùng": ảnh đại diện, tên, email, vùng hành động bên phải.
 *
 * Cùng một dòng này xuất hiện ở kết quả tìm kiếm, danh sách người theo dõi,
 * danh sách đang theo dõi, danh sách thành viên channel và trang quản trị —
 * trước đây mỗi nơi tự dựng lại một kiểu, và ba trong số đó hiện ảnh vỡ khi
 * người dùng chưa đặt ảnh đại diện.
 */
function UserRow({ user, subtitle, actions, onClick, className }) {
  const navigate = useNavigate();
  const goToProfile = () => navigate(`/profile/${user?._id}`);

  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-card bg-surface p-3 ring-1 ring-inset ring-line transition-colors',
        (onClick || user?._id) && 'hover:bg-surface-2',
        className
      )}
    >
      <button
        type='button'
        className='flex min-w-0 flex-1 items-center gap-3 text-left'
        onClick={onClick || goToProfile}
      >
        <Avatar src={user?.avatar} name={user?.username} size='md' />
        <span className='min-w-0'>
          <span className='block truncate text-sm font-semibold text-fg'>
            {user?.username}
          </span>
          {subtitle && (
            <span className='block truncate text-xs text-fg-subtle'>{subtitle}</span>
          )}
        </span>
      </button>
      {actions && <div className='flex shrink-0 items-center gap-2'>{actions}</div>}
    </div>
  );
}

export default UserRow;
