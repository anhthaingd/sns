import cn from '../../services/utils/cn';

/** Một khối xám nhấp nháy giữ đúng chỗ của nội dung sắp tới. */
export function Skeleton({ className, ...rest }) {
  return <div className={cn('fu-skeleton', className)} {...rest} />;
}

/** Khung xương của một thẻ bài viết trên bảng tin. */
export function PostSkeleton() {
  return (
    <div className='rounded-card bg-surface p-4 ring-1 ring-inset ring-line sm:p-5'>
      <div className='flex items-center gap-3'>
        <Skeleton className='size-10 shrink-0 rounded-full' />
        <div className='flex-1 space-y-2'>
          <Skeleton className='h-3 w-32' />
          <Skeleton className='h-2.5 w-20' />
        </div>
      </div>
      <div className='mt-4 space-y-2'>
        <Skeleton className='h-3 w-full' />
        <Skeleton className='h-3 w-11/12' />
        <Skeleton className='h-3 w-2/3' />
      </div>
      <Skeleton className='mt-4 h-40 w-full rounded-lg' />
    </div>
  );
}

/** Khung xương của một thẻ việc làm. */
export function JobSkeleton() {
  return (
    <div className='rounded-card bg-surface p-5 ring-1 ring-inset ring-line'>
      <Skeleton className='h-4 w-3/4' />
      <Skeleton className='mt-2.5 h-3 w-1/3' />
      <div className='mt-4 flex gap-2'>
        <Skeleton className='h-5 w-16 rounded-pill' />
        <Skeleton className='h-5 w-20 rounded-pill' />
        <Skeleton className='h-5 w-14 rounded-pill' />
      </div>
    </div>
  );
}

/** Khung xương của một dòng trong danh sách người dùng / kênh. */
export function RowSkeleton() {
  return (
    <div className='flex items-center gap-3 p-2'>
      <Skeleton className='size-10 shrink-0 rounded-full' />
      <Skeleton className='h-3 w-28' />
    </div>
  );
}

/**
 * Lặp lại một khung xương `count` lần.
 * Dùng `<SkeletonList count={4} item={JobSkeleton} />`.
 */
export function SkeletonList({ count = 3, item: Item = PostSkeleton, className }) {
  return (
    <div className={cn('flex flex-col gap-4', className)} aria-hidden='true'>
      {Array.from({ length: count }, (_, i) => (
        <Item key={i} />
      ))}
    </div>
  );
}

export default Skeleton;
