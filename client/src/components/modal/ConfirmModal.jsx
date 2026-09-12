import { useContext } from 'react';
import { useTranslation } from 'react-i18next';
import { ModalContext } from '../../context/ModalProvider';
import Dialog from '../ui/Dialog';
import Button from '../ui/Button';
import cn from '../../services/utils/cn';

/**
 * Hộp xác nhận dùng chung.
 *
 * Nhận cấu hình qua `setVisibleModal({ visibleConfirmModal: {...} })`:
 *   icon, question, description, loading, acceptFunc, tone ('danger' | 'default')
 *
 * `tone='danger'` tô nút xác nhận màu đỏ son. Bản cũ luôn dùng nút XANH LÁ cho
 * mọi thao tác, kể cả xoá vĩnh viễn bài viết — màu xanh đọc ra là "an toàn,
 * cứ bấm đi", đúng ngược với việc đang xảy ra.
 */
function ConfirmModal() {
  const { t } = useTranslation('common');
  const { state, setVisibleModal } = useContext(ModalContext);
  const config = state.visibleConfirmModal;
  const isDanger = config?.tone === 'danger';

  return (
    <Dialog
      open={Boolean(config)}
      onClose={() => setVisibleModal('visibleConfirmModal')}
      size='sm'
      busy={config?.loading}
      footer={
        <>
          <Button
            variant='outline'
            onClick={() => setVisibleModal('visibleConfirmModal')}
            disabled={config?.loading}
          >
            {t('actions.cancel')}
          </Button>
          <Button
            variant={isDanger ? 'danger' : 'primary'}
            loading={config?.loading}
            onClick={config?.acceptFunc}
          >
            {isDanger ? t('actions.delete') : t('actions.accept')}
          </Button>
        </>
      }
    >
      <div className='flex flex-col items-center gap-4 py-4 text-center'>
        {config?.icon && (
          <span
            className={cn(
              'flex size-12 items-center justify-center rounded-full text-xl',
              isDanger ? 'bg-danger-soft text-danger-text' : 'bg-brand-soft text-brand-text'
            )}
          >
            {config.icon}
          </span>
        )}
        <div className='flex flex-col gap-1.5'>
          <p className='text-base font-bold text-fg'>
            {config?.question || t('confirm.areYouSure')}
          </p>
          {config?.description && (
            <p className='text-sm leading-relaxed text-fg-muted'>
              {config.description}
            </p>
          )}
        </div>
      </div>
    </Dialog>
  );
}

export default ConfirmModal;
