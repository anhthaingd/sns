import { useContext } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaUserGroup, FaRegComment } from 'react-icons/fa6';
import { useGetSearchUsersQuery } from '../../../../services/redux/query/api/usersApi';
import { ModalContext } from '../../../../context/ModalProvider';
import Pagination from '../../../../components/ui/Pagination';
import UserRow from '../../../../components/ui/UserRow';
import Button from '../../../../components/ui/Button';
import EmptyState from '../../../../components/ui/EmptyState';
import { RowSkeleton } from '../../../../components/ui/Skeleton';

function Users({ searchValue }) {
  const { t } = useTranslation(['user', 'common']);
  const { setVisibleModal } = useContext(ModalContext);
  const [searchParams] = useSearchParams();
  const {
    data: usersData,
    isSuccess: isSuccessUsers,
    isLoading,
  } = useGetSearchUsersQuery(
    `page=${searchParams.get('page') || 1}&search=${searchValue}`,
    { skip: !searchValue }
  );

  if (isLoading) {
    return (
      <div aria-hidden='true' className='flex flex-col gap-2'>
        <RowSkeleton />
        <RowSkeleton />
        <RowSkeleton />
      </div>
    );
  }

  if (isSuccessUsers && usersData?.users?.length === 0) {
    return <EmptyState icon={FaUserGroup} title={t('search.empty')} />;
  }

  return (
    <>
      <p className='tnum mb-3 text-sm text-fg-subtle'>
        {t('common:status.foundResults', { count: usersData?.totalUsers || 0 })}
      </p>
      <div className='flex flex-col gap-2'>
        {usersData?.users?.map((u) => (
          <UserRow
            key={u._id}
            user={u}
            subtitle={u?.email}
            actions={
              <Button
                variant='outline'
                size='sm'
                icon={FaRegComment}
                onClick={() => setVisibleModal({ visibleChatModal: u })}
              >
                {t('search.message')}
              </Button>
            }
          />
        ))}
      </div>
      <Pagination
        curPage={searchParams.get('page') || 1}
        totalPage={usersData?.totalPage}
      />
    </>
  );
}

export default Users;
