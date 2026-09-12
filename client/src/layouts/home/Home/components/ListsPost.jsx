import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaRegNewspaper } from 'react-icons/fa6';
import { useGetPostsQuery } from '../../../../services/redux/query/api/postsApi';
import SinglePost from '../../../../components/ui/SinglePost';
import EmptyState from '../../../../components/ui/EmptyState';
import { SkeletonList } from '../../../../components/ui/Skeleton';
import Spinner from '../../../../components/ui/Spinner';
import useObserver from '../../../../hooks/useObserver';

function ListsPost() {
  const { t } = useTranslation(['post', 'common', 'channel']);
  const [changeData, setChangeData] = useState(false);
  const [posts, setPosts] = useState([]);
  const [hasMore, setHasMore] = useState(true);
  const [curPage, setCurPage] = useState(1);
  const {
    data: postsData,
    isSuccess: isSuccessPostsData,
    isLoading,
  } = useGetPostsQuery(`page=${curPage}`);
  const { itemRef } = useObserver(
    hasMore,
    curPage,
    setCurPage,
    isSuccessPostsData,
    postsData?.posts,
    postsData?.totalPage
  );

  const renderedPosts = useMemo(
    () =>
      posts?.map((p) => (
        <SinglePost changeData={setChangeData} key={p._id} post={p} />
      )),
    [posts]
  );

  useEffect(() => {
    if (changeData) {
      setCurPage(1);
      setPosts([]);
      setHasMore(true);
      setChangeData(false);
    }
  }, [changeData]);

  useEffect(() => {
    if (isSuccessPostsData && postsData) {
      setPosts((prevPosts) =>
        curPage === 1 ? [...postsData.posts] : [...prevPosts, ...postsData.posts]
      );
      if (postsData?.totalPage === curPage) {
        setCurPage(postsData?.totalPage);
        setHasMore(false);
      }
    }
  }, [isSuccessPostsData, postsData, curPage, hasMore]);

  // Lần tải đầu tiên dựng khung xương đúng hình dạng bài viết, thay vì phủ
  // trắng cả trang như màn hình chờ toàn cục trước đây.
  if (isLoading && posts.length === 0) {
    return <SkeletonList count={3} />;
  }

  if (!hasMore && posts.length === 0) {
    return (
      <EmptyState
        icon={FaRegNewspaper}
        title={t('empty')}
        description={t('channel:emptyFeedHint')}
      />
    );
  }

  return (
    <div className='flex flex-col gap-4'>
      {renderedPosts}
      {hasMore && (
        <div
          ref={itemRef}
          className='flex items-center justify-center gap-2 py-6 text-sm text-fg-subtle'
        >
          <Spinner className='size-4' />
          <span>{t('common:status.loadingMore')}</span>
        </div>
      )}
    </div>
  );
}

export default ListsPost;
