import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Page from '../../Page';
import Tabs from '../../../components/ui/Tabs';
import SectionHeading from '../../../components/ui/SectionHeading';
import Posts from './components/Posts';
import Followers from './components/Followers';
import Following from './components/Following';

function UserSettingsLayout() {
  const { t } = useTranslation('admin');
  const [curTab, setCurTab] = useState('posts');

  const tabs = useMemo(
    () => [
      { key: 'posts', label: t('settings.tabs.posts') },
      { key: 'followers', label: t('settings.tabs.followers') },
      { key: 'following', label: t('settings.tabs.following') },
    ],
    [t]
  );

  return (
    <Page wide rail={false}>
      <SectionHeading title={t('settings.title')} />
      <Tabs className='mt-5' items={tabs} value={curTab} onChange={setCurTab} />
      <div className='mt-6'>
        {curTab === 'posts' && <Posts />}
        {curTab === 'followers' && <Followers />}
        {curTab === 'following' && <Following />}
      </div>
    </Page>
  );
}

export default UserSettingsLayout;
