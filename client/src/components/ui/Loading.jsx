import React from 'react';
import Spinner from './Spinner';

/**
 * Màn hình chờ toàn trang.
 *
 * Bản cũ phủ một lớp trắng đặc lên cả trang ở MỌI lần gọi API, nên mỗi thao
 * tác đều thấy trang chớp trắng một cái. Ở đây nền trong suốt có làm mờ, giữ
 * lại bố cục phía dưới nên mắt không mất điểm tựa; và nơi nào tải dữ liệu
 * trong một vùng thì nên dùng khung xương (`Skeleton`) chứ đừng gọi cái này.
 */
const Loading = React.memo(function Loading({ label }) {
  return (
    <div
      className='fixed inset-0 z-[90] flex animate-fade-in items-center justify-center bg-bg/70 backdrop-blur-[2px]'
      role='status'
      aria-live='polite'
    >
      <div className='flex flex-col items-center gap-3 rounded-card bg-surface px-8 py-6 shadow-pop ring-1 ring-inset ring-line'>
        <Spinner className='size-7 text-accent' />
        {label && <p className='text-sm font-medium text-fg-muted'>{label}</p>}
      </div>
    </div>
  );
});

export default Loading;
