import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaUserGroup } from 'react-icons/fa6';
import { useGetSearchUsersQuery } from '../../services/redux/query/api/usersApi';
import { useDebounce } from '../../hooks/useDebounce';
import useObserver from '../../hooks/useObserver';
import Popover from '../ui/Popover';
import Avatar from '../ui/Avatar';
import Spinner from '../ui/Spinner';

/**
 * Gợi ý người dùng khi gõ vào ô tìm kiếm trên thanh trên cùng.
 *
 * Bảng này neo vào ô nhập chứ không vào nút, nên `Popover` ở đây được đặt
 * `left-0 right-auto` để mép trái thẳng hàng với ô.
 */
function SearchUsersDropdown({ searchValue, setIsFocus }) {
  const { t } = useTranslation(['user', 'common']);
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
      setUsers((prevUsers) =>
        curPage === 1
          ? [...usersData.users]
          : [...new Set([...prevUsers, ...usersData.users])]
      );
      if (usersData?.totalPage === curPage) setHasMore(false);
    }
  }, [isSuccessUsers, usersData, curPage]);

  const handleRedirect = useCallback(
    (u) => {
      setIsFocus();
      navigate(`/profile/${u?._id}`);
    },
    [navigate, setIsFocus]
  );

  const rendered = useMemo(
    () =>
      users?.map((u) => (
        <li key={u._id}>
          <button
            type='button'
            className='flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-surface-2'
            onClick={() => handleRedirect(u)}
          >
            <Avatar src={u?.avatar} name={u?.username} size='sm' />
            <span className='min-w-0'>
              <span className='block truncate text-sm font-semibold text-fg'>
                {u?.username}
              </span>
              <span className='block truncate text-2xs text-fg-subtle'>
                {u?.email}
              </span>
            </span>
          </button>
        </li>
      )),
    [users, handleRedirect]
  );

  return (
    <Popover
      open
      onClose={setIsFocus}
      title={t('search.title')}
      className='left-0 right-auto'
    >
      {users?.length === 0 ? (
        <div className='flex flex-col items-center gap-2 px-4 py-8 text-center'>
          <FaUserGroup className='size-5 text-fg-subtle' aria-hidden='true' />
          <p className='text-sm text-fg-muted'>{t('search.empty')}</p>
        </div>
      ) : (
        <ul className='flex flex-col gap-0.5'>{rendered}</ul>
      )}
      {hasMore && users?.length > 0 && (
        <div
          ref={itemRef}
          className='flex items-center justify-center gap-2 py-3 text-xs text-fg-subtle'
        >
          <Spinner className='size-3.5' />
          {t('common:status.loadingMore')}
        </div>
      )}
    </Popover>
  );
}

export default SearchUsersDropdown;
