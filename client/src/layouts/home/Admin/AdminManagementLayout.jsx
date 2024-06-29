import React, { Suspense, lazy, useContext, useState } from 'react';
import Page from '../../Page';
import { FetchDataContext } from '../../../context/FetchDataProvider';
import NotFoundLayout from '../../notfound/NotFoundLayout';
const Website = lazy(() => import('./components/Website'));
const Users = lazy(() => import('./components/Users'));
const Channels = lazy(() => import('./components/Channels'));
const UserPosts = lazy(() => import('./components/UserPosts'));
function AdminManagementLayout() {
  const { user } = useContext(FetchDataContext);
  const [curTab, setCurTab] = useState('website');
  if (user && user?.role?.value !== 1) {
    return <NotFoundLayout />;
  }
  return (
    <Page>
      <section className='flex flex-col gap-8'>
        <div className='border border-neutral-300 dark:border-neutral-700 rounded-lg p-4 flex flex-col gap-8'>
          <h1 className='text-xl md:text-2xl font-bold'>Management</h1>
          <div className='flex items-center gap-6'>
            <button
              className={`py-2 ${
                curTab === 'website' ? 'border-b-2 border-blue-500' : ''
              }`}
              onClick={() => setCurTab('website')}
            >
              Website
            </button>
            <button
              className={`py-2 ${
                curTab === 'user' ? 'border-b-2 border-blue-500' : ''
              }`}
              onClick={() => setCurTab('user')}
            >
              Users
            </button>
            <button
              className={`py-2 ${
                curTab === 'channel' ? 'border-b-2 border-blue-500' : ''
              }`}
              onClick={() => setCurTab('channel')}
            >
              Channels
            </button>
            <button
              className={`py-2 ${
                curTab === 'user_posts' ? 'border-b-2 border-blue-500' : ''
              }`}
              onClick={() => setCurTab('user_posts')}
            >
              User Posts
            </button>
          </div>
        </div>
        <Suspense>
          {curTab === 'website' && <Website />}
          {curTab === 'user' && <Users />}
          {curTab === 'channel' && <Channels />}
          {curTab === 'user_posts' && <UserPosts />}
        </Suspense>
      </section>
    </Page>
  );
}

export default AdminManagementLayout;
