import { useContext } from 'react';
import { FetchDataContext } from '../../../../context/FetchDataProvider';
import { useGetPostsQuery } from '../../../../services/redux/query/api/postsApi';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { formatDistance } from 'date-fns';
import { currentDateLocale } from '../../../../i18n/dateLocale';
import Pagination from '../../../../components/ui/Pagination';
import { useTranslation } from 'react-i18next';

function Posts({ searchValue }) {
  const { t } = useTranslation(['post', 'common']);
  const { updateShortcut } = useContext(FetchDataContext);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { data: postsData, isSuccess: isSuccessPosts } = useGetPostsQuery(
    `page=${searchParams.get('page') || 1}&search=${searchValue}`,
    { skip: !searchValue }
  );
  return (
    <div className='p-4 rounded'>
      <div className='flex justify-between items-center gap-4'>
        <h1 className='text-xl md:text-2xl font-bold dark:text-white'>{t('title')}</h1>
        {isSuccessPosts && (
          <p className='text-medium text-lg'>
            {t('common:status.foundResults', { count: postsData?.totalPosts || 0 })}
          </p>
        )}
      </div>
      {isSuccessPosts && postsData?.posts?.length > 0 && (
        <div className='my-8 px-32'>
          <div className='flex flex-col gap-16'>
            {postsData?.posts?.map((p) => {
              return (
                <article
                  className='p-4 border border-neutral-300 dark:border-none dark:bg-neutral-700 rounded-lg flex flex-col gap-4'
                  key={p._id}
                >
                  <div className='flex items-center gap-2'>
                    <img
                      className='size-[42px] rounded-full object-cover'
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
                          onClick={() => {
                            updateShortcut(p?.channel?._id);
                            navigate(
                              `/channels/${p?.channel?._id}/posts/${p?._id}`
                            );
                          }}
                        >
                          {p?.channel?.name}
                        </h2>
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
                              new Date(p?.created_at),
                              new Date(Date.now()),
                              {
                                addSuffix: true,
                                locale: currentDateLocale(),
                              }
                            )}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                  {/* `images` là một object {name, url} hoặc null — KHÔNG phải
                      mảng. Bản cũ viết `p?.images[0]` nên mọi bài không có ảnh
                      (358/374 bài trong DB) làm sập cả trang tìm kiếm. */}
                  {p?.images?.url && (
                    <div>
                      <img
                        className='w-full h-full object-contain'
                        src={`${import.meta.env.VITE_BACKEND_URL}/${p.images.url}`}
                        alt={p.images.name || ''}
                      />
                    </div>
                  )}
                  <div className='w-full flex justify-between'>
                    <p className='text-lg font-medium'>
                      {t('count.like', { count: p?.liked?.length || 0 })}
                    </p>
                    <p className='text-lg font-medium'>
                      {t('count.comment', { count: p?.comments?.length || 0 })}
                    </p>
                  </div>
                </article>
              );
            })}
            {postsData?.totalPage > 1 && (
              <Pagination
                curPage={searchParams.get('page') || 1}
                totalPage={postsData?.totalPage}
              />
            )}
          </div>
        </div>
      )}
      {isSuccessPosts && postsData?.posts?.length === 0 && (
        <div className='my-8'>
          <p className='text-xl font-bold text-center'>{t('empty')}</p>
        </div>
      )}
    </div>
  );
}

export default Posts;
