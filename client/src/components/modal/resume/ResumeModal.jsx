import { useContext, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ModalContext } from '../../../context/ModalProvider';
import Dialog from '../../ui/Dialog';
import Template1 from './Template1';
import Template2 from './Template2';
import cn from '../../../services/utils/cn';

/**
 * Xem trước và in CV.
 *
 * Phần xem trước luôn giữ nền trắng và chữ đen, KHÔNG theo chế độ tối của giao
 * diện: đây là bản sẽ được in ra giấy hoặc xuất PDF, nên nó phải trông đúng
 * như lúc in. Bản cũ để nền `dark:bg-neutral-800` nên người dùng chế độ tối
 * xem trước một tờ CV đen.
 */
function ResumeModal() {
  const { t } = useTranslation('resume');
  const { state, setVisibleModal } = useContext(ModalContext);
  const [curTemplate, setCurTemplate] = useState('1');
  const form = useMemo(() => state.visibleResumeModal || {}, [state.visibleResumeModal]);

  const tabClass = (id) =>
    cn(
      'rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors',
      curTemplate === id
        ? 'bg-brand text-brand-on'
        : 'bg-surface-2 text-fg-muted hover:bg-surface-3 hover:text-fg'
    );

  return (
    <Dialog
      open={Boolean(state.visibleResumeModal)}
      onClose={() => setVisibleModal('visibleResumeModal')}
      title={t('template.title')}
      size='full'
      footer={
        <div className='mr-auto flex items-center gap-2'>
          <button type='button' className={tabClass('1')} onClick={() => setCurTemplate('1')}>
            {t('template.pick1')}
          </button>
          <button type='button' className={tabClass('2')} onClick={() => setCurTemplate('2')}>
            {t('template.pick2')}
          </button>
        </div>
      }
    >
      <div className='rounded-lg bg-white p-2 text-neutral-900 shadow-card sm:p-6'>
        {curTemplate === '1' && <Template1 resume={form} />}
        {curTemplate === '2' && <Template2 resume={form} />}
      </div>
    </Dialog>
  );
}

export default ResumeModal;
