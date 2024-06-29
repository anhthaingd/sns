import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useGetSearchUsersQuery } from '../../services/redux/query/usersQuery';
import { useNavigate } from 'react-router-dom';
import { useDebounce } from '../../hooks/useDebounce';
import useObserver from '../../hooks/useObserver';
import { FaXmark } from 'react-icons/fa6';

function SearchUsersDropdown({ searchValue, setIsFocus }) {
  const debouncedValue = useDebounce(searchValue, 500);
  const navigate = useNavigate();
  const [hasMore, setHasMore] = useState(true);
  const [curPage, setCurPage] = useState(1);
  const [users, setUsers] = useState([]);
  const { data: usersData, isSuccess: isSuccessUsers } = useGetSearchUsersQuery(
    `page=${curPage}&search=${debouncedValue}`
  );
  const { itemRef } = useObserver(
    hasMore,
    curPage,
    setCurPage,
    isSuccessUsers,
    usersData?.users,
    usersData?.totalPage
  );
  useEffect(() => {
    if (debouncedValue) {
      setCurPage(1);
      setUsers([]);
      setHasMore(true);
    }
  }, [debouncedValue]);
  useEffect(() => {
    if (isSuccessUsers && usersData) {
      setUsers((prevUsers) => {
        if (curPage === 1) {
          return [...usersData.users];
        }
        return [...new Set([...prevUsers, ...usersData.users])];
      });

      if (usersData?.totalPage === curPage) {
        setHasMore(false);
      }
    }
  }, [isSuccessUsers, usersData, curPage]);
  const handleRedirect = useCallback(
    (user) => {
      setIsFocus();
      navigate(`/profile/${user?._id}`);
    },
    [navigate]
  );
  const rendered = useMemo(() => {
    return users?.map((u) => {
      return (
        <article
          key={u._id}
          className='cursor-pointer flex gap-2 font-bold'
          onClick={() => handleRedirect(u)}
        >
          <div className='size-[36px] rounded-full overflow-hidden'>
            <img
              className='w-full h-full object-cover'
              src={`${import.meta.env.VITE_BACKEND_URL}/${u?.avatar?.url}`}
              alt={u?.email}
              {...{ fetchPriority: 'low' }}
            />
          </div>
          <p>{u?.username}</p>
        </article>
      );
    });
  }, [users]);
  return (
    <div
      className={`absolute w-[380px] h-[90vh] top-[100%] left-0 my-1 bg-neutral-100 dark:bg-neutral-800 rounded-lg overflow-hidden shadow-lg`}
    >
      <div className='p-4 flex justify-between items-center gap-4'>
        <h2 className='text-lg font-bold'>Search</h2>
        <button aria-label='close-search' onClick={setIsFocus}>
          <FaXmark className='text-2xl' />
        </button>
      </div>
      <div className='p-4 max-h-[80vh] overflow-y-auto'>
        {users?.length === 0 && (
          <div>
            <p>No User Yet!</p>
          </div>
        )}
        <div className='flex flex-col gap-6'>{rendered}</div>
        {hasMore && (
          <div className='text-center my-4' ref={itemRef}>
            Loading more...
          </div>
        )}
      </div>
    </div>
  );
}

export default SearchUsersDropdown;
