import React, { useState } from 'react';
import Page from '../../Page';
import Posts from './components/Posts';
import Followers from './components/Followers';
import Following from './components/Following';
function UserSettingsLayout() {
  const [curTab, setCurTab] = useState('posts');
  return (
    <Page>
      <section className='flex flex-col gap-8'>
        <div className='border border-neutral-300 dark:border-neutral-700 rounded-lg p-4 flex flex-col gap-8'>
          <h1 className='text-xl md:text-2xl font-bold'>Management</h1>
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
          {curTab === 'posts' && <Posts />}
          {curTab === 'followers' && <Followers />}
          {curTab === 'following' && <Following />}
        </div>
      </section>
    </Page>
  );
}

export default UserSettingsLayout;
