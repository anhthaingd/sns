import { NavLink } from 'react-router-dom';
import cn from '../../services/utils/cn';

const itemClass = ({ isActive }) =>
  cn(
    'relative -mb-px whitespace-nowrap border-b-2 px-1 py-2.5 text-sm font-semibold transition-colors duration-150',
    isActive
      ? 'border-accent text-accent-text'
      : 'border-transparent text-fg-subtle hover:border-line-strong hover:text-fg'
  );

/**
 * Thanh tab.
 *
 * Hai chế độ:
 *   - `items` có `to`  → dùng <NavLink>, trạng thái đang chọn lấy từ URL.
 *   - `items` có `key` → tab nội bộ, nơi gọi tự giữ `value` / `onChange`.
 *
 * Cuộn ngang được trên màn hình hẹp thay vì xuống dòng thành hai tầng.
 */
function Tabs({ items = [], value, onChange, className }) {
  return (
    <div
      className={cn(
        'flex gap-6 overflow-x-auto border-b border-line',
        '[scrollbar-width:none] [&::-webkit-scrollbar]:hidden',
        className
      )}
      role={onChange ? 'tablist' : undefined}
    >
      {items.map((item) =>
        item.to ? (
          <NavLink key={item.to} to={item.to} end={item.end} className={itemClass}>
            {item.label}
            {item.count !== undefined && (
              <span className='tnum ml-1.5 text-fg-subtle'>{item.count}</span>
            )}
          </NavLink>
        ) : (
          <button
            key={item.key}
            type='button'
            role='tab'
            aria-selected={value === item.key}
            className={itemClass({ isActive: value === item.key })}
            onClick={() => onChange?.(item.key)}
          >
            {item.label}
            {item.count !== undefined && (
              <span className='tnum ml-1.5 text-fg-subtle'>{item.count}</span>
            )}
          </button>
        )
      )}
    </div>
  );
}

export default Tabs;
