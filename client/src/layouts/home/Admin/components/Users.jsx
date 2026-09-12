import { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useGetUsersByAdminQuery } from '../../../../services/redux/query/api/usersApi';
import useQueryString from '../../../../hooks/useQueryString';
import { formatDate } from '../../../../services/utils/format';
import Table from '../../../../components/ui/Table';
import EmptyState from '../../../../components/ui/EmptyState';
import SearchBar from '../../../../components/ui/SearchBar';
import Avatar from '../../../../components/ui/Avatar';

const cell = 'px-4 py-3 align-middle';

function Users() {
  const { t } = useTranslation(['user', 'common', 'admin']);
  const [searchParams] = useSearchParams();
  const [createQueryString, deleteQueryString] = useQueryString();
  const { data: usersData, isSuccess: isSuccessUsers } = useGetUsersByAdminQuery(
    `page=${searchParams.get('page') || 1}&search=${searchParams.get('search')}`
  );

  const rendered = useMemo(
    () =>
      isSuccessUsers &&
      usersData?.users?.map((u) => (
        <tr key={u._id}>
          <td className={cell}>
            <div className='flex items-center gap-2.5'>
              <Avatar src={u?.avatar} name={u?.username} size='sm' />
              <span className='truncate font-medium text-fg'>{u.username}</span>
            </div>
          </td>
          <td className={`${cell} text-fg-muted`}>{u.email}</td>
          <td className={`${cell} text-fg-muted`}>{u.address}</td>
          <td className={`${cell} tnum whitespace-nowrap text-fg-subtle`}>
            {formatDate(u.created_at)}
          </td>
          {/* Mã người dùng đứng cuối, cỡ chữ nhỏ: nó chỉ cần khi tra cứu sự cố,
              còn bản cũ đặt nó ở cột ĐẦU TIÊN — thứ vô nghĩa nhất với mắt người
              lại chiếm chỗ dễ đọc nhất. */}
          <td className={`${cell} font-mono text-2xs text-fg-subtle`} title={u._id}>
            {u._id}
          </td>
        </tr>
      )),
    [isSuccessUsers, usersData]
  );

  return (
    <div className='flex flex-col gap-4'>
      <SearchBar
        placeholder={t('search.usernamePlaceholder')}
        initialValue={searchParams.get('search') || ''}
        onSearch={(value) => createQueryString('search', value)}
        onReset={deleteQueryString}
      />
      {isSuccessUsers && usersData?.users.length > 0 ? (
        <Table
          tHeader={[
            t('admin:table.username'),
            t('admin:table.email'),
            t('field.address'),
            t('admin:table.createdAt'),
            t('admin:table.id'),
          ]}
          renderedData={rendered}
          currPage={searchParams.get('page') || 1}
          totalPage={usersData?.totalPage}
        />
      ) : (
        isSuccessUsers && <EmptyState title={t('search.empty')} />
      )}
    </div>
  );
}

export default Users;
