import React, { useContext, useMemo } from 'react';
import {
  useBookMarkPostMutation,
  useGetBookMarksQuery,
} from '../../../services/redux/query/usersQuery';
import { FetchDataContext } from '../../../context/FetchDataProvider';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Page from '../../Page';
import { formatDistance } from 'date-fns';
import { IoBookmarkOutline } from 'react-icons/io5';
import Pagination from '../../../components/ui/Pagination';
function BookMarkLayout() {
  const { user } = useContext(FetchDataContext);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { data: bookmarksData, isSuccess: isSuccessBookmarks } =
    useGetBookMarksQuery(`page=${searchParams.get('page') || 1}`, {
      skip: !user,
    });
  const [bookmark] = useBookMarkPostMutation();
  const rendered = useMemo(() => {
    return (
      isSuccessBookmarks &&
      bookmarksData?.posts?.map((p) => {
        return (
          <article
            className='p-4 border border-neutral-300 dark:border-none dark:bg-neutral-800 rounded-lg flex flex-col gap-4'
            key={p._id}
          >
            <div className='flex items-center gap-2'>
              <img
                className='size-[32px] rounded-full object-cover'
                src={`${import.meta.env.VITE_BACKEND_URL}/${
                  p?.user?.avatar?.url
                }`}
                alt={p?.user?.username}
                {...{ fetchPriority: 'low' }}
              />
              <div className='w-full'>
                <div className='w-full flex justify-between'>
                  <h2
                    className='text-[12px] md:text-sm font-bold cursor-pointer'
                    onClick={() =>
                      navigate(`/channels/${p?.channel._id}/posts/${p?._id}`)
                    }
                  >
                    {p?.channel?.name}
                  </h2>
                  <button
                    aria-label='bookmark-btn'
                    onClick={() =>
                      bookmark({ channelId: p?.channel._id, postId: p?._id })
                    }
                  >
                    <IoBookmarkOutline className='text-2xl text-yellow-500' />
                  </button>
                </div>
                <div className='text-neutral-600 dark:text-neutral-400 font-medium text-[12px] md:text-sm flex flex-col sm:flex-row sm:items-center sm:gap-2'>
                  <h3
                    className='cursor-pointer'
                    onClick={() => navigate(`/profile/${p?.user?._id}`)}
                  >
                    {p?.user?.username}
                  </h3>
                  <div className='relative px-2'>
                    <span className='absolute top-1/2 left-0 -translate-y-1/2 w-1 h-1 rounded-full bg-neutral-700 dark:bg-neutral-300'></span>
                    <p>
                      {formatDistance(
                        new Date(p.created_at),
                        new Date(Date.now()),
                        {
                          addSuffix: true,
                        }
                      )}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div dangerouslySetInnerHTML={{ __html: p?.content }}></div>
            <div>
              <img
                className='w-full h-full object-contain'
                src={`${import.meta.env.VITE_BACKEND_URL}/${p?.images?.url}`}
                alt={p?.images?.name}
              />
            </div>
          </article>
        );
      })
    );
  }, [isSuccessBookmarks, bookmarksData]);
  return (
    <Page>
      <div className='flex flex-col gap-8  md:px-16 lg:px-32 xl:px-64'>
        {isSuccessBookmarks && bookmarksData?.posts?.length > 0 && (
          <div className='flex flex-col gap-8'>{rendered}</div>
        )}
        {isSuccessBookmarks && bookmarksData?.posts?.length === 0 && (
          <div className='my-8 full flex justify-center items-end'>
            <p className='text-2xl font-bold'>No Bookmark Yet!</p>
          </div>
        )}
        {isSuccessBookmarks && bookmarksData?.totalPage > 1 && (
          <Pagination
            curPage={searchParams.get('page') || 1}
            totalPage={bookmarksData?.totalPage}
          />
        )}
      </div>
    </Page>
  );
}

export default BookMarkLayout;
