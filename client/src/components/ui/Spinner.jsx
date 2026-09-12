import cn from '../../services/utils/cn';

/** Con quay chờ — kế thừa `currentColor` nên đặt ở đâu cũng đúng màu. */
function Spinner({ className, label }) {
  return (
    <svg
      className={cn('size-5 animate-spin-slow', className)}
      viewBox='0 0 24 24'
      fill='none'
      role={label ? 'status' : 'presentation'}
      aria-label={label}
      aria-hidden={label ? undefined : 'true'}
    >
      <circle
        cx='12'
        cy='12'
        r='9'
        stroke='currentColor'
        strokeWidth='2.5'
        opacity='0.2'
      />
      <path
        d='M21 12a9 9 0 0 0-9-9'
        stroke='currentColor'
        strokeWidth='2.5'
        strokeLinecap='round'
      />
    </svg>
  );
}

export default Spinner;
