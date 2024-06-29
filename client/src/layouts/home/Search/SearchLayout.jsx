import React, { Suspense, lazy, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Page from '../../Page';
import { FaMagnifyingGlass } from 'react-icons/fa6';
import useQueryString from '../../../hooks/useQueryString';
const Users = lazy(() => import('./components/Users'));
const Posts = lazy(() => import('./components/Posts'));
function SearchLayout() {
  const [searchParams, setSearchParams] = useSearchParams();
  const curTab = useMemo(() => {
    return searchParams.get('tab') ? searchParams.get('tab') : 'users';
  }, [searchParams]);
  const [createQueryString, deleteQueryString] = useQueryString();
  const [searchValue, setSearchValue] = useState('');
  const searchInputRef = useRef();
  const handleSearch = () => {
    if (searchValue !== '') {
      createQueryString('s', searchValue);
    } else {
      deleteQueryString();
    }
  };
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSearch();
    }
  };
  return (
    <Page>
      <div className='flex flex-col gap-8'>
        {curTab !== 'recruitment' && (
          <>
            <h1 className='text-2xl font-bold'>Search</h1>
            <div className='relative w-full flex items-center'>
              <FaMagnifyingGlass
                className='absolute top-1/2 right-6 -translate-y-1/2  cursor-pointer text-2xl'
                onClick={handleSearch}
              />
              <input
                ref={searchInputRef}
                className='w-full py-4 px-8 rounded bg-neutral-100 dark:bg-neutral-800 md:text-lg'
                type='text'
                placeholder='Search...'
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                onKeyDown={handleKeyDown}
              />
            </div>
          </>
        )}
        <div className='flex items-center gap-8 text-lg bg-neutral-100 dark:bg-neutral-800 p-4 rounded font-bold'>
          <button
            className={`${curTab === 'users' ? 'text-blue-500' : ''}`}
            onClick={() => createQueryString('tab', 'users')}
          >
            Users
          </button>
          <button
            className={`${curTab === 'posts' ? 'text-blue-500' : ''}`}
            onClick={() => createQueryString('tab', 'posts')}
          >
            Posts
          </button>
        </div>
        <Suspense>
          <div>
            {searchParams.get('s') && curTab === 'users' && (
              <Users searchValue={searchParams.get('s')} />
            )}
            {searchParams.get('s') && curTab === 'posts' && (
              <Posts searchValue={searchParams.get('s')} />
            )}
          </div>
        </Suspense>
      </div>
    </Page>
  );
}

export default SearchLayout;
