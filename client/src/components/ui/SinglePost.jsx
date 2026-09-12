import { formatDistance, formatDistanceStrict } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import {
  Suspense,
  lazy,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { useTranslation } from 'react-i18next';
import {
  FaRegThumbsUp,
  FaThumbsUp,
  FaPaperPlane,
  FaPen,
  FaTrash,
  FaRegTrashCan,
} from 'react-icons/fa6';
import {
  IoChatboxOutline,
  IoBookmarkOutline,
  IoBookmark,
  IoEllipsisHorizontal,
} from 'react-icons/io5';
import { currentDateLocale } from '../../i18n/dateLocale';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { ModalContext } from '../../context/ModalProvider';
import {
  useBookMarkPostMutation,
  useCommentPostMutation,
  useDeleteCommentPostMutation,
  useDeletePostMutation,
  useLikePostMutation,
} from '../../services/redux/query/api/postsApi';
import useMutationToast from '../../hooks/useMutationToast';
import cn from '../../services/utils/cn';
import mediaUrl from '../../services/utils/media';
import Avatar from './Avatar';
import Card from './Card';
import IconButton from './IconButton';

const UpdatePostModal = lazy(() => import('../modal/UpdatePostModal'));

/** Số bình luận hiện sẵn; phần còn lại nằm sau nút "xem tất cả". */
const VISIBLE_COMMENTS = 2;

/** Một nút trong thanh Thích / Bình luận / Lưu. */
function ActionButton({ active, activeClass, icon: Icon, activeIcon: ActiveIcon, label, onClick }) {
  const Glyph = active && ActiveIcon ? ActiveIcon : Icon;
  return (
    <button
      type='button'
      aria-pressed={active}
      className={cn(
        'flex flex-1 items-center justify-center gap-2 rounded-lg py-2 text-sm font-semibold transition-colors duration-150',
        active ? activeClass : 'text-fg-muted hover:bg-surface-2 hover:text-fg'
      )}
      onClick={onClick}
    >
      <Glyph className='size-[1.125rem]' aria-hidden='true' />
      <span>{label}</span>
    </button>
  );
}

function SinglePost({ post, changeData }) {
  const { t } = useTranslation(['post', 'common']);
  const navigate = useNavigate();
  const { user, updateShortcut } = useContext(FetchDataContext);
  const { setVisibleModal } = useContext(ModalContext);
  const [toggleSetting, setToggleSetting] = useState(false);
  const [showAllComments, setShowAllComments] = useState(false);
  const [commentDraft, setCommentDraft] = useState('');
  const menuRef = useRef(null);
  const commentRef = useRef(null);

  const { _id, channel, created_at, content, images, liked, comments, book_marked } = post;

  const [likePost, { isSuccess: isSuccessLikePost }] = useLikePostMutation();
  const [bookMark, { isSuccess: isSuccessBookMark }] = useBookMarkPostMutation();
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

  const handlePostComment = useCallback(async () => {
    const value = commentDraft.trim();
    if (!value) return;
    await postComment({ channelId: channel._id, postId: _id, content: value });
  }, [postComment, commentDraft, channel, _id]);

  useMutationToast({
    data: dataDelete,
    error: errorDelete,
    isSuccess: isSuccessDelete,
    isError: isErrorDelete,
  });
  useMutationToast(
    {
      data: postCommentData,
      error: errorPostComment,
      isSuccess: isSuccessPostComment,
      isError: isErrorPostComment,
    },
    {
      // Bản cũ xoá ô nhập ở NGOÀI nhánh thành công, nên gửi bình luận thất bại
      // cũng mất luôn nội dung vừa gõ. Giờ chỉ xoá khi đã gửi được.
      onSuccess: () => setCommentDraft(''),
    }
  );

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

  // Menu "…" trước đây định vị bằng `-bottom-[400%]`, tức là trôi ra ngoài thẻ
  // và bị thẻ bài kế tiếp che mất. Giờ neo vào góc nút và đóng khi bấm ra ngoài.
  useEffect(() => {
    if (!toggleSetting) return undefined;
    const onPointerDown = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setToggleSetting(false);
    };
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, [toggleSetting]);

  const isOwner = user?._id === post?.user?._id;
  const isLiked = liked?.some((l) => l._id === user?._id);
  const isSaved = book_marked?.some((b) => b._id === user?._id);
  const imageUrl = mediaUrl(images);
  const allComments = comments ?? [];
  const visibleComments = showAllComments
    ? allComments
    : allComments.slice(-VISIBLE_COMMENTS);

  return (
    <>
      <Suspense fallback={null}>
        <UpdatePostModal />
      </Suspense>

      <Card as='article' padded={false} className='overflow-hidden'>
        <header className='flex items-start gap-3 p-4 pb-3'>
          <Avatar src={post?.user?.avatar} name={post?.user?.username} size='md' />
          <div className='min-w-0 flex-1'>
            <button
              type='button'
              className='block max-w-full truncate text-sm font-bold text-fg transition-colors hover:text-accent-text'
              onClick={() => {
                updateShortcut(channel?._id);
                navigate(`/channels/${channel?._id}/posts/${_id}`);
              }}
            >
              {channel?.name}
            </button>
            <div className='flex flex-wrap items-center gap-x-1.5 text-xs text-fg-subtle'>
              <button
                type='button'
                className='font-medium transition-colors hover:text-fg'
                onClick={() => navigate(`/profile/${post?.user?._id}`)}
              >
                {post?.user?.username}
              </button>
              <span aria-hidden='true'>·</span>
              <time dateTime={created_at}>
                {formatDistance(new Date(created_at), new Date(Date.now()), {
                  addSuffix: true,
                  locale: currentDateLocale(),
                })}
              </time>
            </div>
          </div>

          {isOwner && (
            <div className='relative' ref={menuRef}>
              <IconButton
                size='sm'
                label={t('common:actions.edit')}
                onClick={() => setToggleSetting((v) => !v)}
              >
                <IoEllipsisHorizontal className='size-4' />
              </IconButton>
              {toggleSetting && (
                <div className='absolute right-0 top-full z-20 mt-1 w-40 animate-pop overflow-hidden rounded-xl bg-surface p-1 shadow-pop ring-1 ring-inset ring-line'>
                  <button
                    type='button'
                    className='flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg'
                    onClick={() => {
                      setVisibleModal({ visibleUpdatePostModal: post });
                      setToggleSetting(false);
                    }}
                  >
                    <FaPen className='size-3.5' aria-hidden='true' />
                    {t('actions.edit')}
                  </button>
                  <button
                    type='button'
                    className='flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-danger-text transition-colors hover:bg-danger-soft'
                    onClick={() => {
                      setToggleSetting(false);
                      setVisibleModal({
                        visibleConfirmModal: {
                          icon: <FaRegTrashCan />,
                          tone: 'danger',
                          question: t('confirm.delete'),
                          description: t('common:confirm.irreversible'),
                          loading: isLoadingDelete,
                          acceptFunc: () =>
                            deletePost({ channelId: channel._id, postId: post?._id }),
                        },
                      });
                    }}
                  >
                    <FaTrash className='size-3.5' aria-hidden='true' />
                    {t('actions.delete')}
                  </button>
                </div>
              )}
            </div>
          )}
        </header>

        <div
          className='fu-prose px-4 pb-3'
          dangerouslySetInnerHTML={{ __html: content }}
        />

        {/* Bài không có ảnh thì bỏ hẳn thẻ img: để nguyên sẽ thành
            `.../undefined` -> 404 -> biểu tượng ảnh vỡ trên mọi bài. */}
        {imageUrl && (
          <img
            className='max-h-[32rem] w-full bg-surface-2 object-cover'
            src={imageUrl}
            alt={images?.name || ''}
            loading='lazy'
          />
        )}

        {(liked?.length > 0 || allComments.length > 0) && (
          <div className='flex items-center justify-between px-4 pt-3 text-xs font-medium text-fg-subtle'>
            <span className='tnum flex items-center gap-1.5'>
              {liked?.length > 0 && (
                <>
                  <span className='flex size-4 items-center justify-center rounded-full bg-brand text-[0.5rem] text-brand-on'>
                    <FaThumbsUp aria-hidden='true' />
                  </span>
                  {t('count.like', { count: liked.length })}
                </>
              )}
            </span>
            {allComments.length > 0 && (
              <span className='tnum'>
                {t('count.comment', { count: allComments.length })}
              </span>
            )}
          </div>
        )}

        <div className='mx-4 mt-2 flex items-center gap-1 border-t border-line py-1'>
          <ActionButton
            active={isLiked}
            activeClass='text-brand-text bg-brand-soft'
            icon={FaRegThumbsUp}
            activeIcon={FaThumbsUp}
            label={t('actions.like')}
            onClick={() => likePost({ channelId: channel._id, postId: _id })}
          />
          <ActionButton
            icon={IoChatboxOutline}
            label={t('actions.comment')}
            onClick={() => commentRef.current?.focus()}
          />
          <ActionButton
            active={isSaved}
            activeClass='text-warning-text bg-warning-soft'
            icon={IoBookmarkOutline}
            activeIcon={IoBookmark}
            label={t('actions.save')}
            onClick={() => bookMark({ channelId: channel._id, postId: _id })}
          />
        </div>

        <div className='border-t border-line bg-surface-2/40 px-4 py-3'>
          {allComments.length > VISIBLE_COMMENTS && !showAllComments && (
            <button
              type='button'
              className='mb-3 text-xs font-semibold text-accent-text hover:underline'
              onClick={() => setShowAllComments(true)}
            >
              {t('comments.showAll', { count: allComments.length })}
            </button>
          )}

          {visibleComments.length > 0 && (
            <ul className='mb-3 flex max-h-80 flex-col gap-3 overflow-y-auto'>
              {visibleComments.map((c) => (
                <li className='flex gap-2.5' key={c?._id}>
                  <Avatar src={c?.user?.avatar} name={c?.user?.username} size='sm' />
                  <div className='min-w-0 flex-1'>
                    <div className='inline-block max-w-full rounded-2xl rounded-tl-sm bg-surface px-3 py-2 ring-1 ring-inset ring-line'>
                      <button
                        type='button'
                        className='block text-xs font-bold text-fg hover:text-accent-text'
                        onClick={() => navigate(`/profile/${c?.user?._id}`)}
                      >
                        {c?.user?.username}
                      </button>
                      <p className='whitespace-pre-wrap break-words text-sm text-fg'>
                        {c?.content}
                      </p>
                    </div>
                    <div className='mt-1 flex items-center gap-3 pl-3 text-2xs text-fg-subtle'>
                      <time dateTime={c?.created_at}>
                        {t('common:time.ago', {
                          value: formatDistanceStrict(
                            new Date(Date.now()),
                            new Date(c?.created_at),
                            { locale: currentDateLocale() }
                          ),
                        })}
                      </time>
                      {user?._id === c?.user?._id && (
                        <button
                          type='button'
                          className='font-semibold transition-colors hover:text-danger-text'
                          onClick={() =>
                            deleteComment({
                              channelId: channel._id,
                              postId: _id,
                              commentId: c?._id,
                            })
                          }
                        >
                          {t('actions.delete')}
                        </button>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {/* Bản cũ dùng một thẻ <p contentEditable> với placeholder vẽ tay đè
              lên trên. Ô nhập thật thì trình duyệt tự lo placeholder, IME tiếng
              Nhật gõ được, và trình quản lý mật khẩu không nhảy vào. */}
          <div className='flex items-center gap-2.5'>
            <Avatar src={user?.avatar} name={user?.username} size='sm' />
            <div className='relative flex-1'>
              <input
                ref={commentRef}
                type='text'
                className='h-9 w-full rounded-pill bg-surface pl-4 pr-10 text-sm text-fg ring-1 ring-inset ring-line transition-shadow placeholder:text-fg-subtle focus:ring-accent'
                placeholder={t('comments.placeholder')}
                value={commentDraft}
                disabled={isLoadingPostComment}
                onChange={(e) => setCommentDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handlePostComment();
                  }
                }}
              />
              <button
                type='button'
                className='absolute right-1 top-1/2 flex size-7 -translate-y-1/2 items-center justify-center rounded-full text-fg-subtle transition-colors hover:bg-accent-soft hover:text-accent-text disabled:opacity-40'
                aria-label={t('actions.sendComment')}
                disabled={!commentDraft.trim() || isLoadingPostComment}
                onClick={handlePostComment}
              >
                <FaPaperPlane className='size-3.5' />
              </button>
            </div>
          </div>
        </div>
      </Card>
    </>
  );
}

export default SinglePost;
