import { Suspense, lazy, useContext, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Page from '../../Page';
import Tabs from '../../../components/ui/Tabs';
import SectionHeading from '../../../components/ui/SectionHeading';
import { FetchDataContext } from '../../../context/FetchDataProvider';
import NotFoundLayout from '../../notfound/NotFoundLayout';

const Website = lazy(() => import('./components/Website'));
const Users = lazy(() => import('./components/Users'));
const Channels = lazy(() => import('./components/Channels'));
const UserPosts = lazy(() => import('./components/UserPosts'));

function AdminManagementLayout() {
  const { t } = useTranslation('admin');
  const { user } = useContext(FetchDataContext);
  const [curTab, setCurTab] = useState('website');

  const tabs = useMemo(
    () => [
      { key: 'website', label: t('management.tabs.website') },
      { key: 'user', label: t('management.tabs.users') },
      { key: 'channel', label: t('management.tabs.channels') },
      { key: 'user_posts', label: t('management.tabs.userPosts') },
    ],
    [t]
  );

  if (user && user?.role?.value !== 1) return <NotFoundLayout />;

  return (
    <Page wide rail={false}>
      <SectionHeading title={t('management.title')} />
      <Tabs className='mt-5' items={tabs} value={curTab} onChange={setCurTab} />
      <div className='mt-6'>
        <Suspense fallback={null}>
          {curTab === 'website' && <Website />}
          {curTab === 'user' && <Users />}
          {curTab === 'channel' && <Channels />}
          {curTab === 'user_posts' && <UserPosts />}
        </Suspense>
      </div>
    </Page>
  );
}

export default AdminManagementLayout;
