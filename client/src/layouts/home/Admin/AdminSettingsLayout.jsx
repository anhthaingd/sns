import { Suspense, lazy, useContext, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Page from '../../Page';
import Tabs from '../../../components/ui/Tabs';
import SectionHeading from '../../../components/ui/SectionHeading';
import { FetchDataContext } from '../../../context/FetchDataProvider';
import NotFoundLayout from '../../notfound/NotFoundLayout';

const Posts = lazy(() => import('./components/Posts'));
const Followers = lazy(() => import('./components/Followers'));
const Following = lazy(() => import('./components/Following'));

function AdminSettingsLayout() {
  const { t } = useTranslation('admin');
  const { user } = useContext(FetchDataContext);
  const [curTab, setCurTab] = useState('posts');

  const tabs = useMemo(
    () => [
      { key: 'posts', label: t('settings.tabs.posts') },
      { key: 'followers', label: t('settings.tabs.followers') },
      { key: 'following', label: t('settings.tabs.following') },
    ],
    [t]
  );

  if (user && user?.role?.value !== 1) return <NotFoundLayout />;

  return (
    <Page wide rail={false}>
      <SectionHeading title={t('settings.title')} />
      <Tabs className='mt-5' items={tabs} value={curTab} onChange={setCurTab} />
      <div className='mt-6'>
        <Suspense fallback={null}>
          {curTab === 'posts' && <Posts />}
          {curTab === 'followers' && <Followers />}
          {curTab === 'following' && <Following />}
        </Suspense>
      </div>
    </Page>
  );
}

export default AdminSettingsLayout;
