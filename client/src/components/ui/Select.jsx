import { forwardRef } from 'react';
import { FaChevronDown } from 'react-icons/fa6';
import cn from '../../services/utils/cn';
import { controlClass } from './Field';

const SIZES = { sm: 'h-9', md: 'h-10', lg: 'h-12' };

/**
 * Ô chọn. Bỏ mũi tên mặc định của trình duyệt và vẽ lại bằng icon, vì mũi tên
 * gốc trên Windows và macOS khác nhau hẳn.
 */
const Select = forwardRef(function Select(
  { size = 'md', className, children, ...rest },
  ref
) {
  return (
    <div className='relative w-full'>
      <select
        ref={ref}
        className={cn(
          controlClass,
          SIZES[size] ?? SIZES.md,
          'cursor-pointer appearance-none pr-9',
          className
        )}
        {...rest}
      >
        {children}
      </select>
      <FaChevronDown
        className='pointer-events-none absolute right-3 top-1/2 size-3 -translate-y-1/2 text-fg-subtle'
        aria-hidden='true'
      />
    </div>
  );
});

export default Select;
