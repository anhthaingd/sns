import { forwardRef } from 'react';
import cn from '../../services/utils/cn';
import { controlClass } from './Field';

const SIZES = { sm: 'h-9', md: 'h-10', lg: 'h-12' };

/** Ô nhập một dòng. `icon` chừa sẵn chỗ bên trái để chữ không đè lên biểu tượng. */
const Input = forwardRef(function Input(
  { size = 'md', icon: Icon, className, ...rest },
  ref
) {
  const input = (
    <input
      ref={ref}
      className={cn(controlClass, SIZES[size] ?? SIZES.md, Icon && 'pl-9', className)}
      {...rest}
    />
  );
  if (!Icon) return input;
  return (
    <div className='relative w-full'>
      <Icon
        className='pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-fg-subtle'
        aria-hidden='true'
      />
      {input}
    </div>
  );
});

export default Input;
