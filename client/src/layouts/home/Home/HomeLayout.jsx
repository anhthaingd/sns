import React from 'react';
import Page from '../../Page';
import CreatePost from './components/CreatePost';
import ListsPost from './components/ListsPost';

function HomeLayout() {
  return (
    <Page>
      <div className='md:px-16 lg:px-32'>
        <CreatePost />
        <ListsPost />
      </div>
    </Page>
  );
}

export default HomeLayout;
