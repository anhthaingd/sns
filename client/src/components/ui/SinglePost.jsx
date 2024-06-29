import { formatDistance, formatDistanceStrict } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import React, {
  Suspense,
  lazy,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import {
  FaRegThumbsUp,
  FaPaperPlane,
  FaPen,
  FaTrash,
  FaRegTrashCan,
} from 'react-icons/fa6';
import {
  IoChatboxOutline,
  IoBookmarkOutline,
  IoEllipsisHorizontal,
} from 'react-icons/io5';
import { FetchDataContext } from '../../context/FetchDataProvider';
import {
  useBookMarkPostMutation,
  useCommentPostMutation,
  useDeleteCommentPostMutation,
  useDeletePostMutation,
  useLikePostMutation,
} from '../../services/redux/query/usersQuery';
import { ModalContext } from '../../context/ModalProvider';
const UpdatePostModal = lazy(() => import('../modal/UpdatePostModal'));
function SinglePost({ post, changeData }) {
  const navigate = useNavigate();
  const { user, updateShortcut } = useContext(FetchDataContext);
  const { setVisibleModal } = useContext(ModalContext);
  const [toggleSetting, setToggleSetting] = useState(false);
  const [isFocusCmt, setIsFocusCmt] = useState(false);
  const {
    _id,
    channel,
    created_at,
    content,
    images,
    liked,
    comments,
    book_marked,
  } = post;
  const commentRef = useRef();
  const [likePost, { isSuccess: isSuccessLikePost }] = useLikePostMutation();
  const [bookNark, { isSuccess: isSuccessBookMark }] =
    useBookMarkPostMutation();
  const [deleteComment, { isSuccess: isSuccessDeleteComment }] =
    useDeleteCommentPostMutation();
  const [
    postComment,
    {
      data: postCommentData,
      isSuccess: isSuccessPostComment,
      isLoading: isLoadingPostComment,
      isError: isErrorPostComment,
      error: errorPostComment,
    },
  ] = useCommentPostMutation();
  const [
    deletePost,
    {
      data: dataDelete,
      isLoading: isLoadingDelete,
      isSuccess: isSuccessDelete,
      isError: isErrorDelete,
      error: errorDelete,
    },
  ] = useDeletePostMutation();
  const handleFocusComment = () => {
    if (commentRef.current) {
      commentRef.current.focus();
      setIsFocusCmt(true);
    }
  };
  const handleKeyDown = async (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      await postComment({
        channelId: channel._id,
        postId: _id,
        content: commentRef?.current?.textContent,
      });
    }
  };
  const handlePostComment = useCallback(async () => {
    await postComment({
      channelId: channel._id,
      postId: _id,
      content: commentRef?.current?.textContent,
    });
  }, [postComment, commentRef, channel, _id]);
  useEffect(() => {
    if (isSuccessDelete && dataDelete) {
      setVisibleModal({
        visibleToastModal: {
          type: 'success',
          message: dataDelete?.message,
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
    dataDelete,
    isErrorDelete,
    errorDelete,
    setVisibleModal,
  ]);
  useEffect(() => {
    if (isSuccessPostComment && postCommentData) {
      setVisibleModal({
        visibleToastModal: {
          type: 'success',
          message: postCommentData?.message,
        },
      });
    }
    if (commentRef.current) {
      commentRef.current.textContent = '';
    }
    if (isErrorPostComment && errorPostComment) {
      setVisibleModal({
        visibleToastModal: {
          type: 'error',
          message: errorPostComment?.data?.message,
        },
      });
    }
  }, [
    isSuccessPostComment,
    postCommentData,
    isErrorPostComment,
    errorPostComment,
    setVisibleModal,
  ]);
  useEffect(() => {
    if (
      isSuccessLikePost ||
      isSuccessBookMark ||
      isSuccessPostComment ||
      isSuccessDeleteComment
    ) {
      changeData(true);
    }
  }, [
    isSuccessLikePost,
    isSuccessBookMark,
    isSuccessPostComment,
    isSuccessDeleteComment,
  ]);
  return (
    <>
      <Suspense>
        <UpdatePostModal />
      </Suspense>
      {/* <ConfirmModal /> */}
      <article
        className='relative p-4 border border-neutral-300 dark:border-none dark:bg-neutral-800 rounded-lg flex flex-col gap-4'
        key={_id}
        aria-disabled={isLoadingPostComment}
      >
        <div className='relative w-full flex justify-end'>
          {user?._id === post?.user?._id && (
            <>
              <button onClick={() => setToggleSetting(!toggleSetting)}>
                <IoEllipsisHorizontal className='text-xl' />
              </button>
              {toggleSetting && (
                <div className='absolute -bottom-[400%] py-2 px-4 flex flex-col gap-2 border border-neutral-400 rounded'>
                  <button
                    className='text-sm flex items-center gap-2'
                    onClick={() => {
                      setVisibleModal({ visibleUpdatePostModal: post });
                      setToggleSetting(false);
                    }}
                  >
                    <FaPen className='text-sm' />
                    <span>Edit</span>
                  </button>
                  <button
                    className='text-sm flex items-center gap-2'
                    onClick={() =>
                      setVisibleModal({
                        visibleConfirmModal: {
                          icon: <FaRegTrashCan className='text-red-500' />,
                          question: `Are you sure you want to this post?`,
                          description:
                            'You will not be able to restore the recording after deletion',
                          loading: isLoadingDelete,
                          acceptFunc: () =>
                            deletePost({
                              channelId: channel._id,
                              postId: post?._id,
                            }),
                        },
                      })
                    }
                  >
                    <FaTrash className='text-sm' />
                    <span>Delete</span>
                  </button>
                </div>
              )}
            </>
          )}
        </div>
        <div className='flex items-center gap-2'>
          <img
            className='size-[42px] rounded-full object-cover'
            src={`${import.meta.env.VITE_BACKEND_URL}/${
              post?.user?.avatar?.url
            }`}
            alt={post?.user?.username}
            {...{ fetchPriority: 'low' }}
          />
          <div className='w-full'>
            <div className='w-full flex justify-between'>
              <h2
                className='text-[12px] md:text-sm font-bold cursor-pointer'
                onClick={() => {
                  updateShortcut(channel?._id);
                  navigate(`/channels/${channel?._id}/posts/${_id}`);
                }}
              >
                {channel?.name}
              </h2>
            </div>
            <div className='text-neutral-600 dark:text-neutral-400 font-medium text-[12px] md:text-sm flex flex-col sm:flex-row sm:items-center sm:gap-2'>
              <h3
                className='cursor-pointer'
                onClick={() => navigate(`/profile/${post?.user?._id}`)}
              >
                {post?.user?.username}
              </h3>
              <div className='relative px-2'>
                <span className='absolute top-1/2 left-0 -translate-y-1/2 w-1 h-1 rounded-full bg-neutral-700 dark:bg-neutral-300'></span>
                <p>
                  {formatDistance(new Date(created_at), new Date(Date.now()), {
                    addSuffix: true,
                  })}
                </p>
              </div>
            </div>
          </div>
        </div>
        <div dangerouslySetInnerHTML={{ __html: content }}></div>
        <div>
          <img
            className='w-full h-full object-contain'
            src={`${import.meta.env.VITE_BACKEND_URL}/${images?.url}`}
            alt={images?.name}
          />
        </div>
        <div className='w-full flex justify-between'>
          <p className='text-lg font-medium'>
            {liked?.length} {liked?.length > 1 ? 'likes' : 'like'}
          </p>
          <p className='text-lg font-medium'>
            {comments?.length} {comments?.length > 1 ? 'comments' : 'comment'}
          </p>
        </div>
        <div className='py-4 w-full flex justify-between items-center gap-4 border-t border-b border-neutral-300 dark:border-neutral-500'>
          <button
            className={`flex items-center gap-2 ${
              liked?.map((l) => l._id)?.includes(user?._id)
                ? 'text-blue-500'
                : ''
            }`}
            aria-label='like-btn'
            onClick={() => likePost({ channelId: channel._id, postId: _id })}
          >
            <FaRegThumbsUp className='text-2xl' />
            <p>Like</p>
          </button>
          <button className='flex items-center gap-2' aria-label='cmt-btn'>
            <IoChatboxOutline className='text-2xl' />
            <p>Comment</p>
          </button>
          <button
            className={`flex items-center gap-2 ${
              book_marked?.map((b) => b._id).includes(user._id)
                ? 'text-yellow-500'
                : ''
            }`}
            aria-label='mark-btn'
            onClick={() => bookNark({ channelId: channel._id, postId: _id })}
          >
            <IoBookmarkOutline className='text-2xl' />
            <p>Save</p>
          </button>
        </div>
        {/* <div>
        {comments.length > 1 && (
          <button className='font-bold hover:border-b hover:border-neutral-300'>
            View more answers
          </button>
        )}
      </div> */}
        <div className='max-h-[30vh] overflow-y-auto'>
          {comments?.map((c) => {
            return (
              <div className='flex gap-2 mb-4' key={c?._id}>
                <div className='size-[32px] rounded-full overflow-hidden'>
                  <img
                    className='w-full h-full object-cover'
                    {...{ fetchPriority: 'low' }}
                    src={`${import.meta.env.VITE_BACKEND_URL}/${
                      c?.user?.avatar?.url
                    }`}
                    alt={c?.user?.username}
                  />
                </div>
                <div className='flex flex-col gap-2'>
                  <div className='flex items-center gap-2'>
                    <div
                      className='text-sm md:text-base bg-neutral-100 dark:bg-neutral-700 rounded-3xl px-4 py-1 cursor-pointer'
                      onClick={() => navigate(`/profile/${c?.user?._id}`)}
                    >
                      <h5 className='font-bold'>{c?.user?.username}</h5>
                      <p>{c?.content}</p>
                    </div>
                    {user?._id === c?.user?._id && (
                      <button
                        className='text-sm'
                        aria-label='delete-btn'
                        onClick={() =>
                          deleteComment({
                            channelId: channel._id,
                            postId: _id,
                            commentId: c?._id,
                          })
                        }
                      >
                        Delete
                      </button>
                    )}
                  </div>
                  <div className='px-4'>
                    <p className='text-[12px] md:text-sm text-neutral-500 dark:text-neutral-300'>
                      {formatDistanceStrict(
                        new Date(Date.now()),
                        new Date(c?.created_at)
                      )}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        <div className='flex items-center gap-4'>
          <div className='size-[32px] rounded-full overflow-hidden'>
            <img
              className='w-full h-full object-cover'
              src={`${import.meta.env.VITE_BACKEND_URL}/${user?.avatar?.url}`}
              alt={user?.username}
              {...{ fetchPriority: 'low' }}
            />
          </div>
          <div className='relative w-full' onClick={handleFocusComment}>
            <p
              onBlur={() => {
                setIsFocusCmt(false);
              }}
              onKeyDown={handleKeyDown}
              ref={commentRef}
              className='px-4 py-2 rounded-3xl bg-neutral-200 dark:bg-neutral-700'
              contentEditable
            ></p>
            {!isFocusCmt && !commentRef.current?.textContent && (
              <div
                className='absolute top-1/2 left-4 -translate-y-1/2'
                onClick={handleFocusComment}
              >
                <p>Comment as {user?.username}</p>
              </div>
            )}
            <button
              className='absolute bottom-[30%] right-4 z-10 hover:text-blue-500 transition-colors'
              aria-label='send-btn'
              onClick={handlePostComment}
            >
              <FaPaperPlane />
            </button>
          </div>
        </div>
      </article>
    </>
  );
}

export default SinglePost;
