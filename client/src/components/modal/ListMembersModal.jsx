import { useCallback, useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaRegTrashCan } from 'react-icons/fa6';
import { ModalContext } from '../../context/ModalProvider';
import { useDeleteUserFromChannelMutation } from '../../services/redux/query/api/channelsApi';
import useMutationToast from '../../hooks/useMutationToast';
import Dialog from '../ui/Dialog';
import UserRow from '../ui/UserRow';
import IconButton from '../ui/IconButton';
import Badge from '../ui/Badge';

/**
 * Danh sách thành viên của một channel.
 *
 * Bản cũ dựng một cái BẢNG sáu cột trong hộp thoại, cao tối đa 30vh và cuộn
 * ngang — trên điện thoại phải cuộn sang phải mới thấy nút xoá. Danh sách dọc
 * vừa khung mọi cỡ màn hình.
 */
function ListMembersModal() {
  const { t } = useTranslation(['channel', 'common']);
  const { state, setVisibleModal } = useContext(ModalContext);
  const [members, setMembers] = useState([]);
  const [
    deleteUser,
    {
      data: deleteData,
      isSuccess: isSuccessDelete,
      isLoading: isLoadingDelete,
      isError: isErrorDelete,
      error: errorDelete,
    },
  ] = useDeleteUserFromChannelMutation();

  useEffect(() => {
    if (state.visibleListMembersModal) {
      setMembers([...(state.visibleListMembersModal?.members || [])]);
    }
  }, [state.visibleListMembersModal]);

  const closeModal = useCallback(() => {
    setVisibleModal('visibleListMembersModal');
    setMembers([]);
  }, [setVisibleModal]);

  useMutationToast({
    data: deleteData,
    error: errorDelete,
    isSuccess: isSuccessDelete,
    isError: isErrorDelete,
  });

  return (
    <Dialog
      open={Boolean(state.visibleListMembersModal)}
      onClose={closeModal}
      title={t('members.title')}
      description={t('memberCount', { count: members.length })}
      busy={isLoadingDelete}
    >
      <div className='flex flex-col gap-2'>
        {members.map((m) => (
          <UserRow
            key={m._id}
            user={m}
            subtitle={m?.email}
            actions={
              <>
                <Badge tone='neutral' className='capitalize'>
                  {m?.role?.name}
                </Badge>
                <IconButton
                  size='sm'
                  label={t('members.removeUser')}
                  className='hover:bg-danger-soft hover:text-danger-text'
                  onClick={() =>
                    setVisibleModal({
                      visibleConfirmModal: {
                        tone: 'danger',
                        icon: <FaRegTrashCan />,
                        question: t('confirm.removeMember', { name: m?.username }),
                        description: t('common:confirm.irreversible'),
                        loading: isLoadingDelete,
                        acceptFunc: () =>
                          deleteUser({
                            channelId: state.visibleListMembersModal?.channel,
                            userId: m?._id,
                          }),
                      },
                    })
                  }
                >
                  <FaRegTrashCan className='size-4' />
                </IconButton>
              </>
            }
          />
        ))}
      </div>
    </Dialog>
  );
}

export default ListMembersModal;
