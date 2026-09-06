import imgNotFound from '../../assets/permissions_dark_mode.svg';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
function NotFoundLayout() {
  const { t } = useTranslation('common');
  const navigate = useNavigate();
  return (
    <main className='absolute w-full h-[100vh] flex justify-center items-center dark:bg-neutral-900 text-neutral-700 dark:text-neutral-100'>
      <div className='p-4 w-full sm:w-1/2 lg:w-1/3 h-1/2 flex flex-col justify-center items-center gap-4'>
        <div className='size-[150px]'>
          <img
            className='w-full h-full object-cover'
            src={imgNotFound}
            alt={t('notFound.imageAlt')}
          />
        </div>
        <h1 className='text-center font-bold text-lg sm:text-xl'>{t('notFound.title')}</h1>
        <p className='text-center'>{t('notFound.description')}</p>
        <button
          className='px-4 py-2 rounded bg-blue-500 text-neutral-100 font-bold'
          onClick={() => navigate('/', { replace: true })}
        >{t('actions.goToFeed')}</button>
      </div>
    </main>
  );
}

export default NotFoundLayout;
