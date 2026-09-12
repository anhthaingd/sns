import { NavLink } from 'react-router-dom';
import cn from '../../services/utils/cn';

/**
 * Một dòng trong menu điều hướng.
 *
 * Mục đang mở được đánh dấu bằng "dây chuông" — vạch dọc chàm → asagi bên trái
 * — chứ không chỉ bằng nền đậm hơn: nền đậm ở chế độ tối gần như không phân
 * biệt được với nền thường.
 */
function NavLinkItem({ to, end, icon: Icon, label, badge, onNavigate }) {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          'group relative flex items-center gap-3 rounded-lg py-2.5 pl-3.5 pr-3 text-sm font-medium transition-colors duration-150',
          isActive
            ? 'bg-brand-soft font-semibold text-brand-text'
            : 'text-fg-muted hover:bg-surface-2 hover:text-fg'
        )
      }
    >
      {({ isActive }) => (
        <>
          {isActive && <span className='fu-cord' aria-hidden='true' />}
          <Icon
            className={cn(
              'size-[1.125rem] shrink-0 transition-colors',
              isActive ? 'text-accent-text' : 'text-fg-subtle group-hover:text-fg-muted'
            )}
            aria-hidden='true'
          />
          <span className='truncate'>{label}</span>
          {badge > 0 && (
            <span className='tnum ml-auto rounded-pill bg-danger px-1.5 py-0.5 text-2xs font-bold text-white'>
              {badge > 99 ? '99+' : badge}
            </span>
          )}
        </>
      )}
    </NavLink>
  );
}

export default NavLinkItem;
