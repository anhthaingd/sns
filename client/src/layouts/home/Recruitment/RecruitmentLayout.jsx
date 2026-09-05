import React, { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Page from '../../Page';
import Pagination from '../../../components/ui/Pagination';
import Loading from '../../../components/ui/Loading';
import NotFoundItem from '../../../components/ui/NotFoundItem';
import {
  useGetJobFiltersQuery,
  useGetJobsQuery,
} from '../../../services/redux/query/usersQuery';
import JobCard, { LEVEL_LABELS } from './components/JobCard';

/**
 * Danh sách việc làm đọc từ dữ liệu đã được ETL chuẩn hoá.
 *
 * Trước đây trang này nhúng thẳng HTML crawl trực tiếp từ 4 trang nguồn: mỗi
 * lần mở là mở 4 trình duyệt phía server, không tìm kiếm được, không lọc được,
 * và trang nguồn chặn là màn hình trắng. Giờ đọc từ collection `jobs`.
 */
function RecruitmentLayout() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [keyword, setKeyword] = useState(searchParams.get('search') || '');

  const query = useMemo(() => {
    const params = new URLSearchParams();
    params.set('page', searchParams.get('page') || 1);
    ['search', 'prefecture', 'japanese', 'salaryMin'].forEach((key) => {
      const value = searchParams.get(key);
      if (value) params.set(key, value);
    });
    if (searchParams.get('remote') === 'true') params.set('remote', 'true');
    return params.toString();
  }, [searchParams]);

  const { data, isLoading, isSuccess } = useGetJobsQuery(query);
  const { data: filters } = useGetJobFiltersQuery();

  // Cố ý KHÔNG dùng hook useQueryString ở đây: `createQueryString` tự đặt lại
  // page=1 nên phải gọi hai lần cho một thao tác, mà cả hai lần đều đọc cùng
  // một `searchQuery` cũ -> lần sau ghi đè lần trước và bộ lọc vừa chọn bị mất.
  // `deleteQueryString` thì xoá SẠCH mọi tham số, tức là bỏ một bộ lọc sẽ kéo
  // theo mất tất cả bộ lọc khác.
  const setFilter = (key, value) => {
    const next = new URLSearchParams(searchParams.toString());
    if (value) next.set(key, value);
    else next.delete(key);
    // Đổi bộ lọc thì quay về trang 1, nếu không người dùng đang ở trang 8 sẽ
    // thấy danh sách trống mà không hiểu vì sao.
    next.set('page', '1');
    setSearchParams(next);
  };

  const renderedJobs = useMemo(
    () => isSuccess && data?.jobs?.map((job) => <JobCard key={job._id} job={job} />),
    [isSuccess, data]
  );

  if (isLoading) return <Loading />;

  return (
    <Page>
      <section className='mb-6 flex flex-col gap-3'>
        <div className='flex items-baseline justify-between gap-4 flex-wrap'>
          <h1 className='text-2xl font-bold'>Việc làm tại Nhật Bản</h1>
          <p className='text-sm opacity-70'>
            {data?.totalJobs ?? 0} tin tổng hợp từ GaijinPot, DaiJob, Nihongo Engineer, LinkedIn JP
          </p>
        </div>

        <form
          className='flex gap-2'
          onSubmit={(e) => {
            e.preventDefault();
            setFilter('search', keyword.trim());
          }}
        >
          <input
            className='flex-1 px-4 py-2 rounded border border-neutral-300 dark:border-neutral-600 bg-neutral-50 dark:bg-neutral-800'
            placeholder='Tìm theo chức danh, công ty, mô tả...'
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
          <button className='px-4 py-2 rounded bg-blue-500 text-neutral-50 font-medium' type='submit'>
            Tìm
          </button>
        </form>

        <div className='flex flex-wrap gap-2 text-sm'>
          <select
            aria-label='Lọc theo địa điểm'
            className='px-3 py-2 rounded border border-neutral-300 dark:border-neutral-600 bg-neutral-50 dark:bg-neutral-800'
            value={searchParams.get('prefecture') || ''}
            onChange={(e) => setFilter('prefecture', e.target.value)}
          >
            <option value=''>Mọi địa điểm</option>
            {filters?.prefectures?.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>

          <select
            aria-label='Lọc theo tiếng Nhật'
            className='px-3 py-2 rounded border border-neutral-300 dark:border-neutral-600 bg-neutral-50 dark:bg-neutral-800'
            value={searchParams.get('japanese') || ''}
            onChange={(e) => setFilter('japanese', e.target.value)}
          >
            <option value=''>Mọi trình độ tiếng Nhật</option>
            {filters?.japaneseLevels?.map((lv) => (
              <option key={lv} value={lv}>
                {LEVEL_LABELS[lv] || lv}
              </option>
            ))}
          </select>

          <select
            aria-label='Lọc theo lương'
            className='px-3 py-2 rounded border border-neutral-300 dark:border-neutral-600 bg-neutral-50 dark:bg-neutral-800'
            value={searchParams.get('salaryMin') || ''}
            onChange={(e) => setFilter('salaryMin', e.target.value)}
          >
            <option value=''>Mọi mức lương</option>
            <option value='3000000'>Từ 300 man/năm</option>
            <option value='5000000'>Từ 500 man/năm</option>
            <option value='8000000'>Từ 800 man/năm</option>
          </select>

          <label className='flex items-center gap-2 px-3 py-2 rounded border border-neutral-300 dark:border-neutral-600'>
            <input
              type='checkbox'
              checked={searchParams.get('remote') === 'true'}
              onChange={(e) => setFilter('remote', e.target.checked ? 'true' : '')}
            />
            Chỉ việc remote
          </label>
        </div>
      </section>

      {data?.jobs?.length ? (
        <>
          <section className='grid grid-cols-1 lg:grid-cols-2 gap-4'>{renderedJobs}</section>
          <Pagination curPage={data?.curPage || 1} totalPage={data?.totalPage || 1} />
        </>
      ) : (
        <NotFoundItem message="Không tìm thấy việc làm nào khớp bộ lọc." />
      )}
    </Page>
  );
}

export default RecruitmentLayout;
