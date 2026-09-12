import { useContext, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaRegTrashCan, FaRegPenToSquare, FaRegNewspaper } from 'react-icons/fa6';
import {
  useDeletePostMutation,
  useGetPostsByUserQuery,
} from '../../../../services/redux/query/api/postsApi';
import { ModalContext } from '../../../../context/ModalProvider';
import useMutationToast from '../../../../hooks/useMutationToast';
import UpdatePostModal from '../../../../components/modal/UpdatePostModal';
import Table from '../../../../components/ui/Table';
import IconButton from '../../../../components/ui/IconButton';
import EmptyState from '../../../../components/ui/EmptyState';
import { formatDate } from '../../../../services/utils/format';
import mediaUrl from '../../../../services/utils/media';

const cell = 'px-4 py-3 align-middle';

function Posts() {
  const { t } = useTranslation(['post', 'common', 'admin']);
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

  const rendered = useMemo(
    () =>
      isSuccessPosts &&
      postsData?.posts?.map((p) => {
        const image = mediaUrl(p?.images);
        return (
          <tr key={p._id}>
            <td className={cell}>
              {/* Ảnh thu nhỏ 40px: bảng là để quét nhanh, ô ảnh 72px như bản cũ
                  đẩy chiều cao mỗi hàng lên gấp ba mà không nói thêm điều gì. */}
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
            <td className={`${cell} max-w-xs`}>
              <div
                className='fu-prose line-clamp-2 text-sm'
                dangerouslySetInnerHTML={{ __html: p?.content }}
              />
            </td>
            <td className={`${cell} whitespace-nowrap text-fg-muted`}>
              {p?.channel?.name}
            </td>
            <td className={`${cell} tnum text-right`}>{p?.liked?.length ?? 0}</td>
            <td className={`${cell} tnum text-right`}>{p?.comments?.length ?? 0}</td>
            <td className={`${cell} tnum text-right`}>{p?.book_marked?.length ?? 0}</td>
            <td className={`${cell} tnum whitespace-nowrap text-fg-subtle`}>
              {formatDate(p?.updated_at)}
            </td>
            <td className={cell}>
              <div className='flex items-center justify-end gap-1'>
                <IconButton
                  size='sm'
                  label={t('actions.edit')}
                  onClick={() => setVisibleModal({ visibleUpdatePostModal: { ...p } })}
                >
                  <FaRegPenToSquare className='size-3.5' />
                </IconButton>
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
    // Bản cũ gọi useMemo KHÔNG có mảng phụ thuộc, tức là tính lại mỗi lần
    // render — đúng kết quả nhưng vô nghĩa. Liệt kê đủ để nó thật sự có tác
    // dụng, và để đổi ngôn ngữ thì nhãn nút cũng đổi theo.
    [isSuccessPosts, postsData, isLoadingDelete, deletePost, setVisibleModal, t]
  );

  useMutationToast({
    data: deleteData,
    error: errorDelete,
    isSuccess: isSuccessDelete,
    isError: isErrorDelete,
  });

  if (isSuccessPosts && postsData?.posts?.length === 0) {
    return <EmptyState icon={FaRegNewspaper} title={t('empty')} />;
  }

  return (
    <div aria-busy={isLoadingDelete}>
      <UpdatePostModal />
      {isSuccessPosts && (
        <Table
          tHeader={[
            t('admin:table.image'),
            t('title'),
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
      )}
    </div>
  );
}

export default Posts;
