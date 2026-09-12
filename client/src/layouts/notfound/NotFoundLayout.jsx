import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaCompass } from 'react-icons/fa6';
import Button from '../../components/ui/Button';

function NotFoundLayout() {
  const { t } = useTranslation('common');
  const navigate = useNavigate();

  return (
    <main className='relative flex min-h-screen items-center justify-center overflow-hidden bg-bg px-4'>
      <div
        className='fu-seigaiha pointer-events-none absolute inset-0 text-fg opacity-[0.05]'
        aria-hidden='true'
      />
      <div className='relative flex w-full max-w-md flex-col items-center gap-4 text-center'>
        <span className='flex size-16 items-center justify-center rounded-full bg-brand-soft text-2xl text-brand-text'>
          <FaCompass aria-hidden='true' />
        </span>
        <h1 className='font-display text-2xl font-black text-fg'>
          {t('notFound.title')}
        </h1>
        <p className='text-sm leading-relaxed text-fg-muted'>
          {t('notFound.description')}
        </p>
        <Button className='mt-2' onClick={() => navigate('/', { replace: true })}>
          {t('actions.goToFeed')}
        </Button>
      </div>
    </main>
  );
}

export default NotFoundLayout;
