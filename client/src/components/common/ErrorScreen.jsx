import { useEffect } from 'react';
import { useRouteError, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { logger } from '../../services/logger';
import { FaTriangleExclamation } from 'react-icons/fa6';
import Button from '../ui/Button';

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
  const { t } = useTranslation(['error', 'common']);
  const error = useRouteError();
  const navigate = useNavigate();

  useEffect(() => {
    logger.error('render.crash', {
      message: error?.message || String(error),
      stack: error?.stack,
    });
  }, [error]);

  return (
    <section className='flex min-h-screen w-full items-center justify-center bg-bg p-4'>
      <div className='flex w-full max-w-lg flex-col items-center gap-4 text-center'>
        <span className='flex size-14 items-center justify-center rounded-full bg-danger-soft text-xl text-danger-text'>
          <FaTriangleExclamation aria-hidden='true' />
        </span>
        <h1 className='font-display text-2xl font-black text-fg'>{t('ui.title')}</h1>
        <p className='text-sm leading-relaxed text-fg-muted'>
          {t('ui.description')}
        </p>

        {/* Chi tiết kỹ thuật chỉ hiện lúc phát triển — người dùng cuối không
            cần, mà stack trace còn có thể lộ đường dẫn nội bộ. */}
        {import.meta.env.DEV && error && (
          <pre
            aria-label={t('ui.technicalDetails')}
            className='max-h-60 w-full overflow-auto rounded-lg bg-surface-2 p-3 text-left text-xs text-fg-muted'
          >
            {error?.stack || error?.message || String(error)}
          </pre>
        )}

        <div className='mt-1 flex flex-wrap justify-center gap-2'>
          <Button onClick={() => window.location.reload()}>
            {t('common:actions.reload')}
          </Button>
          <Button variant='outline' onClick={() => navigate('/')}>
            {t('common:actions.goHome')}
          </Button>
        </div>
      </div>
    </section>
  );
}

export default ErrorScreen;
