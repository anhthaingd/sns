import { useContext } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaRegTrashCan, FaUserGroup } from 'react-icons/fa6';
import {
  useDeleteFollowersMutation,
  useGetFollowersQuery,
} from '../../../../services/redux/query/api/usersApi';
import { ModalContext } from '../../../../context/ModalProvider';
import useMutationToast from '../../../../hooks/useMutationToast';
import Pagination from '../../../../components/ui/Pagination';
import UserRow from '../../../../components/ui/UserRow';
import IconButton from '../../../../components/ui/IconButton';
import EmptyState from '../../../../components/ui/EmptyState';
import { RowSkeleton } from '../../../../components/ui/Skeleton';

/**
 * Người theo dõi mình.
 *
 * Bản cũ nhét danh sách người vào một BẢNG bốn cột (email / ảnh / tên / thao
 * tác) với ảnh đại diện 72px trong ô — bảng là để so sánh số liệu giữa các
 * hàng, còn đây chỉ là danh bạ. Dạng danh sách đọc nhanh hơn và vừa màn hình
 * điện thoại.
 */
function Followers() {
  const { t } = useTranslation(['user', 'common']);
  const [searchParams] = useSearchParams();
  const { setVisibleModal } = useContext(ModalContext);
  const {
    data: followersData,
    isSuccess: isSuccessFollowers,
    isLoading,
  } = useGetFollowersQuery(`page=${searchParams.get('page') || 1}`);
  const [
    deleteUser,
    {
      data: deleteData,
      isSuccess: isSuccessDelete,
      isLoading: isLoadingDelete,
      isError: isErrorDelete,
      error: errorDelete,
    },
  ] = useDeleteFollowersMutation();

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

  if (isSuccessFollowers && followersData?.followers?.length === 0) {
    return <EmptyState icon={FaUserGroup} title={t('followers.empty')} />;
  }

  return (
    <div aria-busy={isLoadingDelete}>
      <div className='flex flex-col gap-2'>
        {followersData?.followers?.map((f) => (
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
                      question: t('confirm.removeFollower', { name: f?.username }),
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
        totalPage={followersData?.totalPage}
      />
    </div>
  );
}

export default Followers;
