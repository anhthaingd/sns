import Modal from '@/modal';
import { useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { ModalContext } from '../../context/ModalProvider';
import { FaXmark, FaRegTrashCan } from 'react-icons/fa6';
import useClickOutside from '../../hooks/useClickOutside';
import { useDeleteUserFromChannelMutation } from '../../services/redux/query/usersQuery';
function ListMembersModal() {
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
      setMembers([...state.visibleListMembersModal?.members]);
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
                title='Delete User'
                className='text-lg flex justify-center items-center hover:text-red-500 transition-colors'
                aria-label='delete-btn'
                onClick={() =>
                  setVisibleModal({
                    visibleConfirmModal: {
                      icon: <FaRegTrashCan className='text-red-500' />,
                      question: `Are you sure you want to remove ${m?.name} from chanel?`,
                      description:
                        'You will not be able to restore the recording after deletion',
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
  }, [members]);
  useEffect(() => {
    if (isSuccessDelete && deleteData) {
      setVisibleModal({
        visibleToastModal: {
          type: 'success',
          message: deleteData?.message,
        },
      });
    }
    if (isErrorDelete && errorDelete) {
      setVisibleModal({
        visibleToastModal: {
          type: 'error',
          message: errorDelete?.data?.message,
        },
      });
    }
  }, [
    isSuccessDelete,
    deleteData,
    isErrorDelete,
    errorDelete,
    setVisibleModal,
  ]);
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
            <h1 className='text-xl md:text-2xl font-bold'>Members</h1>
            <button aria-label='close-list' onClick={closeModal}>
              <FaXmark className='text-2xl' />
            </button>
          </div>
          <div className='w-full max-h-[30vh] border border-neutral-300 dark:border-neutral-700 overflow-x-auto overflow-y-auto'>
            <table className='relative w-full h-full whitespace-nowrap'>
              <thead>
                <tr className='border-b border-neutral-300 dark:border-neutral-700 font-medium'>
                  <td className='p-4 text-center'>SR</td>
                  <td className='p-4 text-center'>USERNAME</td>
                  <td className='p-4 text-center'>AVATAR</td>
                  <td className='p-4 text-center'>EMAIL</td>
                  <td className='p-4 text-center'>ROLE</td>
                  <td className='p-4 text-center'>ACTIONS</td>
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
