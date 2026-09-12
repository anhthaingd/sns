import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaRegNewspaper } from 'react-icons/fa6';
import { useGetPostsQuery } from '../../../../services/redux/query/api/postsApi';
import Pagination from '../../../../components/ui/Pagination';
import SinglePost from '../../../../components/ui/SinglePost';
import EmptyState from '../../../../components/ui/EmptyState';
import { SkeletonList } from '../../../../components/ui/Skeleton';

/**
 * Kết quả tìm kiếm bài viết.
 *
 * Dùng `SinglePost` thay cho thẻ bài rút gọn tự vẽ như bản cũ — thẻ cũ hiện
 * lượt thích và bình luận nhưng không bấm được vào đâu cả, kể cả để mở bài.
 */
function Posts({ searchValue }) {
  const { t } = useTranslation(['post', 'common']);
  const [searchParams] = useSearchParams();
  const {
    data: postsData,
    isSuccess: isSuccessPosts,
    isLoading,
    refetch,
  } = useGetPostsQuery(`page=${searchParams.get('page') || 1}&search=${searchValue}`, {
    skip: !searchValue,
  });

  if (isLoading) return <SkeletonList count={2} />;

  if (isSuccessPosts && postsData?.posts?.length === 0) {
    return <EmptyState icon={FaRegNewspaper} title={t('empty')} />;
  }

  return (
    <>
      <p className='tnum mb-3 text-sm text-fg-subtle'>
        {t('common:status.foundResults', { count: postsData?.totalPosts || 0 })}
      </p>
      <div className='mx-auto flex w-full max-w-feed flex-col gap-4'>
        {postsData?.posts?.map((p) => (
          <SinglePost key={p._id} post={p} changeData={refetch} />
        ))}
        <Pagination
          curPage={searchParams.get('page') || 1}
          totalPage={postsData?.totalPage}
        />
      </div>
    </>
  );
}

export default Posts;
