import { useContext } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaRegTrashCan, FaUserGroup } from 'react-icons/fa6';
import {
  useDeleteFollowingMutation,
  useGetFollowingQuery,
} from '../../../../services/redux/query/api/usersApi';
import { ModalContext } from '../../../../context/ModalProvider';
import useMutationToast from '../../../../hooks/useMutationToast';
import Pagination from '../../../../components/ui/Pagination';
import UserRow from '../../../../components/ui/UserRow';
import IconButton from '../../../../components/ui/IconButton';
import EmptyState from '../../../../components/ui/EmptyState';
import { RowSkeleton } from '../../../../components/ui/Skeleton';

/**
 * Những người mình đang theo dõi. Cùng dạng danh sách với `Followers`, chỉ
 * khác nguồn dữ liệu và câu xác nhận khi bỏ theo dõi.
 */
function Following() {
  const { t } = useTranslation(['user', 'common']);
  const [searchParams] = useSearchParams();
  const { setVisibleModal } = useContext(ModalContext);
  const {
    data: followingData,
    isSuccess: isSuccessFollowing,
    isLoading,
  } = useGetFollowingQuery(`page=${searchParams.get('page') || 1}`);
  const [
    deleteUser,
    {
      data: deleteData,
      isSuccess: isSuccessDelete,
      isLoading: isLoadingDelete,
      isError: isErrorDelete,
      error: errorDelete,
    },
  ] = useDeleteFollowingMutation();

  useMutationToast({
    data: deleteData,
    error: errorDelete,
    isSuccess: isSuccessDelete,
    isError: isErrorDelete,
  });

  if (isLoading) {
    return (
      <div aria-hidden='true' className='flex flex-col gap-2'>
        <RowSkeleton />
        <RowSkeleton />
      </div>
    );
  }

  if (isSuccessFollowing && followingData?.following?.length === 0) {
    return <EmptyState icon={FaUserGroup} title={t('following.empty')} />;
  }

  return (
    <div aria-busy={isLoadingDelete}>
      <div className='flex flex-col gap-2'>
        {followingData?.following?.map((f) => (
          <UserRow
            key={f?._id}
            user={f}
            subtitle={f?.email}
            actions={
              <IconButton
                size='sm'
                label={t('actions.delete')}
                className='hover:bg-danger-soft hover:text-danger-text'
                onClick={() =>
                  setVisibleModal({
                    visibleConfirmModal: {
                      tone: 'danger',
                      icon: <FaRegTrashCan />,
                      question: t('confirm.unfollow', { name: f?.username }),
                      description: t('common:confirm.irreversible'),
                      loading: isLoadingDelete,
                      acceptFunc: () => deleteUser(f?._id),
                    },
                  })
                }
              >
                <FaRegTrashCan className='size-4' />
              </IconButton>
            }
          />
        ))}
      </div>
      <Pagination
        curPage={searchParams.get('page') || 1}
        totalPage={followingData?.totalPage}
      />
    </div>
  );
}

export default Following;
