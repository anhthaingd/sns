import React, { useContext, useEffect, useMemo } from 'react';
import {
  useDeletePostMutation,
  useGetPostsByUserQuery,
} from '../../../../services/redux/query/usersQuery';
import { useSearchParams } from 'react-router-dom';
import Table from '../../../../components/ui/Table';
import { formatDate } from '../../../../services/utils/format';
import { FaRegTrashCan, FaRegPenToSquare } from 'react-icons/fa6';
import { ModalContext } from '../../../../context/ModalProvider';
import UpdatePostModal from '../../../../components/modal/UpdatePostModal';

function Posts() {
  const [searchParams] = useSearchParams();
  const { setVisibleModal } = useContext(ModalContext);
  const { data: postsData, isSuccess: isSuccessPosts } = useGetPostsByUserQuery(
    `page=${searchParams.get('page') || 1}`
  );
  const [
    deletePost,
    {
      data: deleteData,
      isSuccess: isSuccessDelete,
      isLoading: isLoadingDelete,
      isError: isErrorDelete,
      error: errorDelete,
    },
  ] = useDeletePostMutation();
  const rendered = useMemo(() => {
    return (
      isSuccessPosts &&
      postsData?.posts?.map((p) => {
        return (
          <tr key={p._id}>
            <td
              title={p?._id}
              className='p-4 text-center truncate max-w-[120px]'
            >
              {p?._id}
            </td>
            <td className='p-4'>
              <div className='m-auto size-[72px] overflow-hidden'>
                <img
                  className='w-full h-full object-cover'
                  src={`${import.meta.env.VITE_BACKEND_URL}/${p?.images?.url}`}
                  alt={p?.images?.name}
                />
              </div>
            </td>
            <td className='p-4 text-center'>{p?.liked?.length}</td>
            <td className='p-4 text-center'>{p?.book_marked?.length}</td>
            <td className='p-4 text-center'>{p?.comments?.length}</td>
            <td className='p-4 text-center'>{p?.channel?.name}</td>
            <td className='p-4 text-center'>{formatDate(p?.updated_at)}</td>
            <td className='p-4'>
              <div className='flex justify-center items-center gap-[12px]'>
                <button
                  className='text-lg flex justify-center items-center hover:text-green-500 transition-colors'
                  aria-label='update-btn'
                  onClick={() =>
                    setVisibleModal({
                      visibleUpdatePostModal: { ...p },
                    })
                  }
                >
                  <FaRegPenToSquare />
                </button>
                <button
                  className='text-lg flex justify-center items-center hover:text-red-500 transition-colors'
                  aria-label='delete-btn'
                  onClick={() =>
                    setVisibleModal({
                      visibleConfirmModal: {
                        icon: <FaRegTrashCan className='text-red-500' />,
                        question: `Are you sure you want to delete this post?`,
                        description:
                          'You will not be able to restore the recording after deletion',
                        loading: isLoadingDelete,
                        acceptFunc: () =>
                          deletePost({
                            channelId: p?.channel?._id,
                            postId: p?._id,
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
      {isSuccessPosts && postsData?.posts?.length > 0 && (
        <Table
          tHeader={[
            'id',
            'images',
            'liked',
            'bookmarked',
            'comments',
            'channel',
            'updated at',
            'actions',
          ]}
          currPage={searchParams.get('page') || 1}
          totalPage={postsData?.totalPage}
          renderedData={rendered}
        />
      )}
      {isSuccessPosts && postsData?.posts?.length === 0 && (
        <div className='w-full flex justify-center items-center py-4'>
          <p className='text-lg md:text-xl font-bold'>No Post Yet!</p>
        </div>
      )}
    </div>
  );
}

export default Posts;
