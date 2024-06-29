import React, { useMemo, useState } from 'react';
import { useGetUsersByAdminQuery } from '../../../../services/redux/query/usersQuery';
import { useSearchParams } from 'react-router-dom';
import { formatDate } from '../../../../services/utils/format';
import Table from '../../../../components/ui/Table';
import NotFoundItem from '../../../../components/ui/NotFoundItem';
import useQueryString from '../../../../hooks/useQueryString';

function Users() {
  const [searchParams] = useSearchParams();
  const [createQueryString, deleteQueryString] = useQueryString();
  const [searchValue, setSearchValue] = useState('');
  const { data: usersData, isSuccess: isSuccessUsers } =
    useGetUsersByAdminQuery(
      `page=${searchParams.get('page') || 1}&search=${searchParams.get(
        'search'
      )}`
    );
  const rendered = useMemo(() => {
    return (
      isSuccessUsers &&
      usersData?.users?.map((u) => {
        return (
          <tr key={u._id}>
            <td
              title={u._id}
              className='p-4 text-center truncate max-w-[120px]'
            >
              {u._id}
            </td>
            <td className='p-4 text-center'>{u.username}</td>
            <td className='p-4 text-center'>{u.email}</td>
            <td className='p-4 text-center'>{u.address}</td>
            <td className='p-4 text-center'>{formatDate(u.created_at)}</td>
          </tr>
        );
      })
    );
  }, [isSuccessUsers, usersData]);
  return (
    <div className='flex flex-col gap-4'>
      <div className='w-full justify-end flex items-center gap-2'>
        <input
          className='px-4 py-2 border border-neutral-300 dark:border-neutral-700 rounded dark:bg-neutral-800'
          type='text'
          placeholder='Search username...'
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
        />
        <button
          className='px-4 py-2 font-bold bg-neutral-700 text-white rounded'
          onClick={deleteQueryString}
        >
          Reset
        </button>
        <button
          className='px-4 py-2 font-bold bg-blue-500 rounded text-neutral-100'
          onClick={() => createQueryString('search', searchValue)}
        >
          Search
        </button>
      </div>
      {isSuccessUsers && usersData?.users.length > 0 && (
        <Table
          tHeader={['id', 'username', 'email', 'address', 'created at']}
          renderedData={rendered}
          currPage={searchParams.get('page') || 1}
          totalPage={usersData?.totalPage}
        />
      )}
      {isSuccessUsers && usersData?.users?.length === 0 && (
        <NotFoundItem message={'No User Yet!'} />
      )}
    </div>
  );
}

export default Users;
