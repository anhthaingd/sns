import { useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  FaRegTrashCan,
  FaRegPenToSquare,
  FaChevronDown,
  FaRegNewspaper,
} from 'react-icons/fa6';
import { useGetAllChannelsQuery } from '../../../../services/redux/query/api/channelsApi';
import {
  useDeletePostByAdminMutation,
  useGetPostsByAdminQuery,
} from '../../../../services/redux/query/api/postsApi';
import { ModalContext } from '../../../../context/ModalProvider';
import { FetchDataContext } from '../../../../context/FetchDataProvider';
import useObserver from '../../../../hooks/useObserver';
import useMutationToast from '../../../../hooks/useMutationToast';
import { formatDate } from '../../../../services/utils/format';
import mediaUrl from '../../../../services/utils/media';
import UpdatePostModal from '../../../../components/modal/UpdatePostModal';
import Table from '../../../../components/ui/Table';
import Badge from '../../../../components/ui/Badge';
import Avatar from '../../../../components/ui/Avatar';
import Button from '../../../../components/ui/Button';
import IconButton from '../../../../components/ui/IconButton';
import EmptyState from '../../../../components/ui/EmptyState';

const cell = 'px-4 py-3 align-middle';

function UserPosts() {
  const { t } = useTranslation(['post', 'common', 'admin']);
  const { user } = useContext(FetchDataContext);
  const [searchParams] = useSearchParams();
  const { setVisibleModal } = useContext(ModalContext);
  const [channels, setChannels] = useState([]);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [openSelect, setOpenSelect] = useState(false);
  const selectRef = useRef(null);
  const { data: postsData, isSuccess: isSuccessPosts } = useGetPostsByAdminQuery(
    `page=${searchParams.get('page') || 1}&channel=${selectedChannel?._id || null}`
  );
  const [hasMore, setHasMore] = useState(true);
  const [curPage, setCurPage] = useState(1);
  const { data: channelsData, isSuccess: isSuccessChannels } = useGetAllChannelsQuery(
    `page=${curPage}`
  );
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
      setChannels((prevChannels) =>
        curPage === 1
          ? [...channelsData.channels]
          : [...new Set([...prevChannels, ...channelsData.channels])]
      );
      if (channelsData?.totalPage === curPage) setHasMore(false);
    }
  }, [isSuccessChannels, channelsData, curPage]);

  // Bản cũ chỉ đóng danh sách channel khi bấm đúng vào một mục trong đó; bấm ra
  // ngoài thì nó nằm đè lên bảng cho tới khi bấm lại nút.
  useEffect(() => {
    if (!openSelect) return undefined;
    const onPointerDown = (e) => {
      if (selectRef.current && !selectRef.current.contains(e.target)) {
        setOpenSelect(false);
      }
    };
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, [openSelect]);

  const rendered = useMemo(
    () =>
      isSuccessPosts &&
      postsData?.posts?.map((p) => {
        const image = mediaUrl(p?.images);
        const isMine = p?.user?._id === user?._id;
        return (
          <tr key={p._id}>
            <td className={cell}>
              <div className='flex items-center gap-2.5'>
                <Avatar src={p?.user?.avatar} name={p?.user?.username} size='sm' />
                <div className='min-w-0'>
                  <p className='truncate font-medium text-fg'>
                    {isMine ? t('admin:userPosts.you') : p?.user?.username}
                  </p>
                  <p className='truncate text-2xs capitalize text-fg-subtle'>
                    {p?.user?.role?.name}
                  </p>
                </div>
              </div>
            </td>
            <td className={cell}>
              {image ? (
                <img
                  className='size-10 rounded-lg object-cover ring-1 ring-inset ring-line'
                  src={image}
                  alt=''
                  loading='lazy'
                />
              ) : (
                <span className='block size-10 rounded-lg bg-surface-2' aria-hidden='true' />
              )}
            </td>
            <td className={`${cell} whitespace-nowrap`}>
              <Badge tone='neutral'>{p?.channel?.name}</Badge>
            </td>
            <td className={`${cell} tnum text-right`}>{p?.liked?.length ?? 0}</td>
            <td className={`${cell} tnum text-right`}>{p?.comments?.length ?? 0}</td>
            <td className={`${cell} tnum text-right`}>{p?.book_marked?.length ?? 0}</td>
            <td className={`${cell} tnum whitespace-nowrap text-fg-subtle`}>
              {formatDate(p?.updated_at)}
            </td>
            <td className={cell}>
              <div className='flex items-center justify-end gap-1'>
                {isMine && (
                  <IconButton
                    size='sm'
                    label={t('actions.edit')}
                    onClick={() => setVisibleModal({ visibleUpdatePostModal: { ...p } })}
                  >
                    <FaRegPenToSquare className='size-3.5' />
                  </IconButton>
                )}
                <IconButton
                  size='sm'
                  label={t('actions.delete')}
                  className='hover:bg-danger-soft hover:text-danger-text'
                  onClick={() =>
                    setVisibleModal({
                      visibleConfirmModal: {
                        tone: 'danger',
                        icon: <FaRegTrashCan />,
                        question: t('confirm.delete'),
                        description: t('common:confirm.irreversible'),
                        loading: isLoadingDelete,
                        acceptFunc: () =>
                          deletePost({ channelId: p?.channel?._id, postId: p?._id }),
                      },
                    })
                  }
                >
                  <FaRegTrashCan className='size-3.5' />
                </IconButton>
              </div>
            </td>
          </tr>
        );
      }),
    // `t` phải nằm trong mảng phụ thuộc: đổi ngôn ngữ thì react-i18next trả về
    // một `t` mới, thiếu nó thì bảng đã memo hoá giữ nguyên chữ của ngôn ngữ cũ.
    [isSuccessPosts, postsData, user, setVisibleModal, deletePost, isLoadingDelete, t]
  );

  useMutationToast({
    data: deleteData,
    error: errorDelete,
    isSuccess: isSuccessDelete,
    isError: isErrorDelete,
  });

  return (
    <div className='flex flex-col gap-4' aria-busy={isLoadingDelete}>
      <UpdatePostModal />

      {/* Danh sách channel dài và tải dần theo cuộn, nên không dùng <select>
          gốc được — phải là danh sách tự vẽ để gắn được bộ quan sát cuộn. */}
      <div className='relative w-max' ref={selectRef}>
        <Button
          variant='outline'
          iconRight={FaChevronDown}
          aria-expanded={openSelect}
          onClick={() => setOpenSelect((prev) => !prev)}
        >
          {selectedChannel ? selectedChannel?.name : t('admin:userPosts.selectChannel')}
        </Button>
        {openSelect && (
          <div className='absolute left-0 top-full z-20 mt-1 max-h-[22rem] w-64 animate-pop overflow-y-auto rounded-card bg-surface p-1.5 shadow-pop ring-1 ring-inset ring-line'>
            <button
              type='button'
              className='flex w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg'
              onClick={() => {
                setOpenSelect(false);
                setSelectedChannel(null);
              }}
            >
              {t('actions.selectAll')}
            </button>
            {channels?.map((c) => (
              <button
                key={c._id}
                type='button'
                className='flex w-full truncate rounded-lg px-3 py-2 text-left text-sm font-medium text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg'
                onClick={() => {
                  setOpenSelect(false);
                  setSelectedChannel(c);
                }}
              >
                {c?.name}
              </button>
            ))}
            {hasMore && (
              <p ref={itemRef} className='py-2 text-center text-xs text-fg-subtle'>
                {t('common:status.loadingMore')}
              </p>
            )}
          </div>
        )}
      </div>

      {isSuccessPosts && postsData?.posts?.length > 0 ? (
        <Table
          tHeader={[
            t('admin:table.user'),
            t('admin:table.image'),
            t('admin:table.channel'),
            t('admin:table.likes'),
            t('admin:table.comments'),
            t('admin:table.bookmarks'),
            t('admin:table.updatedAt'),
            t('admin:table.actions'),
          ]}
          currPage={searchParams.get('page') || 1}
          totalPage={postsData?.totalPage}
          renderedData={rendered}
        />
      ) : (
        isSuccessPosts && <EmptyState icon={FaRegNewspaper} title={t('empty')} />
      )}
    </div>
  );
}

export default UserPosts;
