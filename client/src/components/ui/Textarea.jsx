import { forwardRef } from 'react';
import cn from '../../services/utils/cn';
import { controlClass } from './Field';

const Textarea = forwardRef(function Textarea({ className, rows = 4, ...rest }, ref) {
  return (
    <textarea
      ref={ref}
      rows={rows}
      className={cn(controlClass, 'resize-y py-2 leading-relaxed', className)}
      {...rest}
    />
  );
});

export default Textarea;
