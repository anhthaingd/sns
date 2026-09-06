import Modal from '@/modal';
import { useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { ModalContext } from '../../context/ModalProvider';
import { FaXmark, FaRegTrashCan } from 'react-icons/fa6';
import useClickOutside from '../../hooks/useClickOutside';
import { useDeleteUserFromChannelMutation } from '../../services/redux/query/api/channelsApi';
import useMutationToast from '../../hooks/useMutationToast';
import { useTranslation } from 'react-i18next';
function ListMembersModal() {
  const { t } = useTranslation(['channel', 'common']);
  const { state, setVisibleModal } = useContext(ModalContext);
  const [modalRef, clickOutside] = useClickOutside();
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
  const rendered = useMemo(() => {
    return members?.map((m, index) => {
      return (
        <tr key={m._id}>
          <td className='p-4 text-center'>{index + 1}</td>
          <td className='p-4 text-center'>{m?.username}</td>
          <td className='p-4'>
            <div className='m-auto size-[36px] rounded-full overflow-hidden'>
              <img
                className='w-full h-full object-cover'
                src={`${import.meta.env.VITE_BACKEND_URL}/${m?.avatar?.url}`}
                alt={m?.avatar?.name}
                {...{ fetchPriority: 'low' }}
              />
            </div>
          </td>
          <td className='p-4 text-center'>{m?.email}</td>
          <td className='p-4 text-center capitalize'>{m?.role?.name}</td>
          <td>
            <div className='flex justify-center items-center gap-[12px]'>
              <button
                title={t('members.removeUser')}
                className='text-lg flex justify-center items-center hover:text-red-500 transition-colors'
                aria-label={t('members.removeUser')}
                onClick={() =>
                  setVisibleModal({
                    visibleConfirmModal: {
                      icon: <FaRegTrashCan className='text-red-500' />,
                      question: t('confirm.removeMember', { name: m?.name }),
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
                <FaRegTrashCan />
              </button>
            </div>
          </td>
        </tr>
      );
    });
  // `t` phải nằm trong mảng phụ thuộc: đổi ngôn ngữ thì react-i18next trả về
  // một `t` mới, thiếu nó thì danh sách đã memo hoá giữ nguyên chữ của ngôn
  // ngữ cũ cho tới khi có thứ khác kích hoạt tính lại.
  }, [members, t]);
  useMutationToast({
    data: deleteData,
    error: errorDelete,
    isSuccess: isSuccessDelete,
    isError: isErrorDelete,
  });
  return (
    <Modal>
      <section
        style={{ backgroundColor: 'rgba(51,51,51,0.9)' }}
        className={`fixed right-0 top-0 w-full h-full z-[100] flex justify-center items-center overflow-hidden transition-all duration-200 ${
          state.visibleListMembersModal ? 'scale-100' : 'scale-0'
        } `}
        onClick={clickOutside}
        aria-disabled={isLoadingDelete}
      >
        <div
          className='bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-100 rounded flex flex-col gap-8 border border-neutral-300 dark:border-neutral-700'
          ref={modalRef}
          aria-disabled={isLoadingDelete}
        >
          <div className='px-4 pt-8 flex justify-between items-center'>
            <h1 className='text-xl md:text-2xl font-bold'>{t('members.title')}</h1>
            <button aria-label={t('members.close')} onClick={closeModal}>
              <FaXmark className='text-2xl' />
            </button>
          </div>
          <div className='w-full max-h-[30vh] border border-neutral-300 dark:border-neutral-700 overflow-x-auto overflow-y-auto'>
            <table className='relative w-full h-full whitespace-nowrap'>
              <thead>
                <tr className='border-b border-neutral-300 dark:border-neutral-700 font-medium'>
                  <td className='p-4 text-center'>{t('members.columns.no')}</td>
                  <td className='p-4 text-center'>{t('members.columns.username')}</td>
                  <td className='p-4 text-center'>{t('members.columns.avatar')}</td>
                  <td className='p-4 text-center'>{t('members.columns.email')}</td>
                  <td className='p-4 text-center'>{t('members.columns.role')}</td>
                  <td className='p-4 text-center'>{t('members.columns.actions')}</td>
                </tr>
              </thead>
              <tbody>{rendered}</tbody>
            </table>
          </div>
        </div>
      </section>
    </Modal>
  );
}

export default ListMembersModal;
