import React, { Suspense, lazy, useContext, useState } from 'react';
import Page from '../../Page';
import { FetchDataContext } from '../../../context/FetchDataProvider';
import NotFoundLayout from '../../notfound/NotFoundLayout';
const Posts = lazy(() => import('./components/Posts'));
const Followers = lazy(() => import('./components/Followers'));
const Following = lazy(() => import('./components/Following'));
function AdminSettingsLayout() {
  const { user } = useContext(FetchDataContext);
  const [curTab, setCurTab] = useState('posts');
  if (user && user?.role?.value !== 1) {
    return <NotFoundLayout />;
  }
  return (
    <Page>
      <section className='flex flex-col gap-8'>
        <div className='border border-neutral-300 dark:border-neutral-700 rounded-lg p-4 flex flex-col gap-8'>
          <h1 className='text-xl md:text-2xl font-bold'>Settings</h1>
          <div className='flex items-center gap-6'>
            <button
              className={`py-2 ${
                curTab === 'posts' ? 'border-b-2 border-blue-500' : ''
              }`}
              onClick={() => setCurTab('posts')}
            >
              Posts
            </button>
            <button
              className={`py-2 ${
                curTab === 'followers' ? 'border-b-2 border-blue-500' : ''
              }`}
              onClick={() => setCurTab('followers')}
            >
              Followers
            </button>
            <button
              className={`py-2 ${
                curTab === 'following' ? 'border-b-2 border-blue-500' : ''
              }`}
              onClick={() => setCurTab('following')}
            >
              Following
            </button>
          </div>
        </div>
        <div>
          <Suspense>
            {curTab === 'posts' && <Posts />}
            {curTab === 'followers' && <Followers />}
            {curTab === 'following' && <Following />}
          </Suspense>
        </div>
      </section>
    </Page>
  );
}

export default AdminSettingsLayout;
