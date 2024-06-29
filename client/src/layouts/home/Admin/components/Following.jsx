import React, { useContext, useEffect, useMemo } from 'react';
import {
  useDeleteFollowingMutation,
  useGetFollowingQuery,
} from '../../../../services/redux/query/usersQuery';
import { useSearchParams } from 'react-router-dom';
import Table from '../../../../components/ui/Table';
import { FaRegTrashCan } from 'react-icons/fa6';
import { ModalContext } from '../../../../context/ModalProvider';
import UpdatePostModal from '../../../../components/modal/UpdatePostModal';

function Following() {
  const [searchParams] = useSearchParams();
  const { setVisibleModal } = useContext(ModalContext);
  const { data: followingData, isSuccess: isSuccessFollowing } =
    useGetFollowingQuery(`page=${searchParams.get('page') || 1}`);
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
  const rendered = useMemo(() => {
    return (
      isSuccessFollowing &&
      followingData?.following?.map((f) => {
        return (
          <tr key={f?._id}>
            <td className='p-4 text-center'>{f?.email}</td>
            <td className='p-4'>
              <div className='m-auto size-[72px] overflow-hidden'>
                <img
                  className='w-full h-full object-cover'
                  src={`${import.meta.env.VITE_BACKEND_URL}/${f?.avatar?.url}`}
                  alt={f?.avatar?.name}
                />
              </div>
            </td>
            <td className='p-4 text-center'>{f?.username}</td>
            <td className='p-4'>
              <div className='flex justify-center items-center gap-[12px]'>
                {/* <button
                  className='text-lg flex justify-center items-center hover:text-green-500 transition-colors'
                  aria-label='update-btn'
                  onClick={() =>
                    setVisibleModal({
                      visibleUpdatePostModal: { ...p },
                    })
                  }
                >
                  <FaRegPenToSquare />
                </button> */}
                <button
                  className='text-lg flex justify-center items-center hover:text-red-500 transition-colors'
                  aria-label='delete-btn'
                  onClick={() =>
                    setVisibleModal({
                      visibleConfirmModal: {
                        icon: <FaRegTrashCan className='text-red-500' />,
                        question: `Are you sure you want to unfollow ${f?.username}?`,
                        description:
                          'You will not be able to restore the recording after deletion',
                        loading: isLoadingDelete,
                        acceptFunc: () => deleteUser(f._id),
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
      })
    );
  });
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
    <div aria-disabled={isLoadingDelete}>
      <UpdatePostModal />
      {isSuccessFollowing && followingData?.following?.length > 0 && (
        <Table
          tHeader={['email', 'avatar', 'username', 'actions']}
          currPage={searchParams.get('page') || 1}
          totalPage={followingData?.totalPage}
          renderedData={rendered}
        />
      )}
      {isSuccessFollowing && followingData?.following?.length === 0 && (
        <div className='w-full flex justify-center items-center py-4'>
          <p className='text-lg md:text-xl font-bold'>No Following Yet!</p>
        </div>
      )}
    </div>
  );
}

export default Following;
