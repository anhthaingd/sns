import { useEffect } from 'react';
import { useRouteError, useNavigate } from 'react-router-dom';
import { logger } from '../../services/logger';

/**
 * Màn hình hiển thị khi một route ném lỗi lúc render.
 *
 * Trước khi có file này, mọi lỗi render đều rơi vào màn hình mặc định của
 * React Router — nền trắng, tiếng Anh, kèm stack trace và dòng chữ "Hey
 * developer". Người dùng cuối không hiểu gì, còn lập trình viên thì không có
 * bản ghi nào ở server để tra lại.
 *
 * Được gắn làm `errorElement` của route gốc nên nó bắt lỗi của mọi route con.
 */
function ErrorScreen() {
  const error = useRouteError();
  const navigate = useNavigate();

  useEffect(() => {
    logger.error('render.crash', {
      message: error?.message || String(error),
      stack: error?.stack,
    });
  }, [error]);

  return (
    <section className='w-full min-h-screen flex items-center justify-center p-4 dark:bg-neutral-900'>
      <div className='w-full max-w-lg flex flex-col gap-4 text-center dark:text-neutral-100'>
        <h1 className='text-2xl font-bold'>Trang gặp sự cố</h1>
        <p className='text-neutral-600 dark:text-neutral-400'>
          Đã có lỗi xảy ra khi hiển thị nội dung. Sự cố đã được ghi nhận, bạn
          thử tải lại trang giúp nhé.
        </p>

        {/* Chi tiết kỹ thuật chỉ hiện lúc phát triển — người dùng cuối không
            cần, mà stack trace còn có thể lộ đường dẫn nội bộ. */}
        {import.meta.env.DEV && error && (
          <pre className='text-left text-xs overflow-auto max-h-60 p-3 rounded bg-neutral-100 dark:bg-neutral-800'>
            {error?.stack || error?.message || String(error)}
          </pre>
        )}

        <div className='flex gap-3 justify-center'>
          <button
            className='px-4 py-2 rounded font-bold bg-blue-500 text-white hover:bg-blue-700 transition-colors'
            onClick={() => window.location.reload()}
          >
            Tải lại trang
          </button>
          <button
            className='px-4 py-2 rounded font-bold border border-neutral-300 dark:border-neutral-700'
            onClick={() => navigate('/')}
          >
            Về trang chủ
          </button>
        </div>
      </div>
    </section>
  );
}

export default ErrorScreen;
