import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaRegNewspaper } from 'react-icons/fa6';
import { useGetPostsInChannelQuery } from '../../../../../services/redux/query/api/postsApi';
import SinglePost from '../../../../../components/ui/SinglePost';
import EmptyState from '../../../../../components/ui/EmptyState';
import Spinner from '../../../../../components/ui/Spinner';
import { SkeletonList } from '../../../../../components/ui/Skeleton';
import useObserver from '../../../../../hooks/useObserver';

function ListsPost({ channelId }) {
  const { t } = useTranslation(['common', 'post']);
  const [changeData, setChangeData] = useState(false);
  const [posts, setPosts] = useState([]);
  const [hasMore, setHasMore] = useState(true);
  const [curPage, setCurPage] = useState(1);
  const {
    data: postsData,
    isSuccess: isSuccessPostsData,
    isLoading,
  } = useGetPostsInChannelQuery({
    channelId: channelId,
    search: `page=${curPage}`,
  });
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
      setPosts([]);
      setHasMore(true);
      setChangeData(false);
      setCurPage(1);
    }
  }, [changeData]);

  useEffect(() => {
    if (isSuccessPostsData && postsData) {
      setPosts((prevPosts) =>
        curPage === 1 ? [...postsData.posts] : [...prevPosts, ...postsData.posts]
      );
      if (postsData?.totalPage === curPage) setHasMore(false);
    }
  }, [isSuccessPostsData, postsData, curPage]);

  if (isLoading && posts.length === 0) return <SkeletonList count={2} />;

  if (!hasMore && posts.length === 0) {
    return <EmptyState icon={FaRegNewspaper} title={t('post:empty')} />;
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
          <span>{t('status.loadingMore')}</span>
        </div>
      )}
    </div>
  );
}

export default ListsPost;
