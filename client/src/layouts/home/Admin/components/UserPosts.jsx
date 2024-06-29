import React, { useContext, useEffect, useMemo, useState } from 'react';
import {
  useDeletePostByAdminMutation,
  useGetAllChannelsQuery,
  useGetPostsByAdminQuery,
} from '../../../../services/redux/query/usersQuery';
import { useSearchParams } from 'react-router-dom';
import Table from '../../../../components/ui/Table';
import { formatDate } from '../../../../services/utils/format';
import { FaRegTrashCan, FaRegPenToSquare } from 'react-icons/fa6';
import { ModalContext } from '../../../../context/ModalProvider';
import UpdatePostModal from '../../../../components/modal/UpdatePostModal';
import { FetchDataContext } from '../../../../context/FetchDataProvider';
import useObserver from '../../../../hooks/useObserver';

function UserPosts() {
  const { user } = useContext(FetchDataContext);
  const [searchParams] = useSearchParams();
  const { setVisibleModal } = useContext(ModalContext);
  const [channels, setChannels] = useState([]);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [openSelect, setOpenSelect] = useState(false);
  const { data: postsData, isSuccess: isSuccessPosts } =
    useGetPostsByAdminQuery(
      `page=${searchParams.get('page') || 1}&channel=${
        selectedChannel?._id || null
      }`
    );
  const [hasMore, setHasMore] = useState(true);
  const [curPage, setCurPage] = useState(1);
  const { data: channelsData, isSuccess: isSuccessChannels } =
    useGetAllChannelsQuery(`page=${curPage}`);
  const { itemRef } = useObserver(
    hasMore,
    curPage,
    setCurPage,
    isSuccessChannels,
    channelsData?.channels,
    channelsData?.totalPage
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
  ] = useDeletePostByAdminMutation();

  useEffect(() => {
    if (isSuccessChannels && channelsData) {
      setChannels((prevChannels) => {
        if (curPage === 1) {
          return [...channelsData.channels];
        }
        return [...new Set([...prevChannels, ...channelsData.channels])];
      });

      if (channelsData?.totalPage === curPage) {
        setHasMore(false);
      }
    }
  }, [isSuccessChannels, channelsData, curPage]);

  const rendered = useMemo(() => {
    return (
      isSuccessPosts &&
      postsData?.posts?.map((p) => (
        <tr key={p._id}>
          <td title={p?._id} className='p-4 text-center truncate max-w-[120px]'>
            {p?._id}
          </td>
          <td title={p?._id} className='p-4 text-center truncate max-w-[120px]'>
            {p?.user?._id === user?._id ? 'You' : p?.user?.username}
          </td>
          <td className='p-4 text-center truncate max-w-[120px] capitalize'>
            {p?.user?.role?.name}
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
              {p?.user?._id === user?._id && (
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
              )}
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
      ))
    );
  }, [
    isSuccessPosts,
    postsData,
    user,
    setVisibleModal,
    deletePost,
    isLoadingDelete,
  ]);

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
      <div className='relative my-4'>
        <button
          className='w-max px-4 py-2 rounded-lg border border-neutral-300 dark:border-neutral-600 font-bold'
          onClick={() => setOpenSelect((prevOpen) => !prevOpen)}
        >
          {selectedChannel ? selectedChannel?.name : 'Select Channel'}
        </button>
        <div
          className={`absolute top-[110%] z-10 h-[40vh] overflow-y-auto flex-col gap-4 rounded-lg border border-neutral-300 dark:border-neutral-600 py-4 bg-white dark:bg-neutral-900 ${
            openSelect ? 'flex' : 'hidden'
          }`}
        >
          <button
            className='px-4 flex justify-start'
            onClick={() => {
              setOpenSelect(false);
              setSelectedChannel(null);
            }}
          >
            <span className='w-max truncate'>Select All</span>
          </button>
          {channels?.map((c) => (
            <button
              key={c._id}
              className='px-4 flex justify-start'
              onClick={() => {
                setOpenSelect(false);
                setSelectedChannel(c);
              }}
            >
              <span className='w-max truncate'>{c?.name}</span>
            </button>
          ))}
          {hasMore && (
            <p className='text-center' ref={itemRef}>
              Loading more...
            </p>
          )}
        </div>
      </div>
      {isSuccessPosts && postsData?.posts?.length > 0 && (
        <Table
          tHeader={[
            'id',
            'user',
            'role',
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

export default UserPosts;
