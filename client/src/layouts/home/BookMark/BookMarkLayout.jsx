import { useContext } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { IoBookmarkOutline } from 'react-icons/io5';
import Page from '../../Page';
import Pagination from '../../../components/ui/Pagination';
import SinglePost from '../../../components/ui/SinglePost';
import EmptyState from '../../../components/ui/EmptyState';
import LinkButton from '../../../components/ui/LinkButton';
import SectionHeading from '../../../components/ui/SectionHeading';
import { SkeletonList } from '../../../components/ui/Skeleton';
import { useGetBookMarksQuery } from '../../../services/redux/query/api/postsApi';
import { FetchDataContext } from '../../../context/FetchDataProvider';

/**
 * Bài đã lưu.
 *
 * Dùng thẳng `SinglePost` thay vì vẽ lại một thẻ bài rút gọn như bản cũ. Thẻ
 * cũ chép lại phần đầu bài viết nhưng bỏ mất thích, bình luận và menu sửa —
 * nên bài ở trang này trông giống mà lại làm được ít việc hơn hẳn, và mỗi lần
 * sửa thẻ bài phải nhớ sửa ở hai nơi.
 */
function BookMarkLayout() {
  const { t } = useTranslation(['post', 'nav']);
  const { user } = useContext(FetchDataContext);
  const [searchParams] = useSearchParams();
  const {
    data: bookmarksData,
    isSuccess: isSuccessBookmarks,
    isLoading,
    refetch,
  } = useGetBookMarksQuery(`page=${searchParams.get('page') || 1}`, {
    skip: !user,
  });

  return (
    <Page>
      <div className='mx-auto flex w-full max-w-feed flex-col gap-4'>
        <SectionHeading title={t('nav:bookmark')} />

        {isLoading && <SkeletonList count={2} />}

        {isSuccessBookmarks &&
          (bookmarksData?.posts?.length > 0 ? (
            <>
              {bookmarksData.posts.map((p) => (
                <SinglePost key={p._id} post={p} changeData={refetch} />
              ))}
              <Pagination
                curPage={searchParams.get('page') || 1}
                totalPage={bookmarksData?.totalPage}
              />
            </>
          ) : (
            <EmptyState
              icon={IoBookmarkOutline}
              title={t('bookmark.empty')}
              action={
                <LinkButton to='/' variant='accent' size='sm'>
                  {t('nav:home')}
                </LinkButton>
              }
            />
          ))}
      </div>
    </Page>
  );
}

export default BookMarkLayout;
