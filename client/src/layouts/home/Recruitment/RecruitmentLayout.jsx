import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaMagnifyingGlass, FaFilter, FaXmark, FaBriefcase } from 'react-icons/fa6';
import Page from '../../Page';
import Pagination from '../../../components/ui/Pagination';
import EmptyState from '../../../components/ui/EmptyState';
import SectionHeading from '../../../components/ui/SectionHeading';
import Button from '../../../components/ui/Button';
import Field from '../../../components/ui/Field';
import Select from '../../../components/ui/Select';
import Badge from '../../../components/ui/Badge';
import { JobSkeleton, SkeletonList } from '../../../components/ui/Skeleton';
import {
  useGetJobFiltersQuery,
  useGetJobsQuery,
} from '../../../services/redux/query/api/jobsApi';
import JobCard from './components/JobCard';
import { japaneseLevelLabel } from '../../../services/utils/jobFormat';
import cn from '../../../services/utils/cn';

/** Những tham số URL được coi là bộ lọc (không tính `page`). */
const FILTER_KEYS = ['search', 'prefecture', 'japanese', 'salaryMin', 'remote'];

/**
 * Danh sách việc làm đọc từ dữ liệu đã được ETL chuẩn hoá.
 *
 * Trước đây trang này nhúng thẳng HTML crawl trực tiếp từ 4 trang nguồn: mỗi
 * lần mở là mở 4 trình duyệt phía server, không tìm kiếm được, không lọc được,
 * và trang nguồn chặn là màn hình trắng. Giờ đọc từ collection `jobs`.
 *
 * Bố cục: cột bộ lọc dính bên trái (từ lg), danh sách kết quả bên phải. Bản
 * cũ xếp bốn ô lọc thành một hàng ngang phía trên rồi để kết quả tràn hai cột
 * — chọn xong bộ lọc phải cuộn xuống mới biết còn bao nhiêu tin.
 */
function RecruitmentLayout() {
  const { t } = useTranslation(['job', 'common']);
  const [searchParams, setSearchParams] = useSearchParams();
  const [keyword, setKeyword] = useState(searchParams.get('search') || '');
  const [filtersOpen, setFiltersOpen] = useState(false);

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

  const { data, isLoading, isFetching, isSuccess } = useGetJobsQuery(query);
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

  const activeFilters = FILTER_KEYS.map((key) => [key, searchParams.get(key)]).filter(
    ([, value]) => Boolean(value)
  );

  const clearAll = () => {
    setKeyword('');
    setSearchParams(new URLSearchParams({ page: '1' }));
  };

  const labelOfFilter = (key, value) => {
    if (key === 'japanese') return japaneseLevelLabel(t, value);
    if (key === 'remote') return t('filter.remoteOnly');
    if (key === 'salaryMin') return t(`filter.from${Math.round(value / 10000)}`);
    return value;
  };

  const renderedJobs = useMemo(
    () => isSuccess && data?.jobs?.map((job) => <JobCard key={job._id} job={job} />),
    [isSuccess, data]
  );

  return (
    <Page wide rail={false}>
      <SectionHeading
        title={t('title')}
        description={t('subtitle', { count: data?.totalJobs ?? 0 })}
        actions={
          <Button
            variant='outline'
            size='sm'
            icon={FaFilter}
            className='lg:hidden'
            onClick={() => setFiltersOpen((v) => !v)}
            aria-expanded={filtersOpen}
          >
            {t('filter.filters')}
            {activeFilters.length > 0 && (
              <span className='tnum ml-1 rounded-pill bg-accent px-1.5 text-2xs text-accent-on'>
                {activeFilters.length}
              </span>
            )}
          </Button>
        }
      />

      <div className='mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[16rem_minmax(0,1fr)]'>
        {/* Cột bộ lọc — dính khi cuộn trên desktop, gập lại trên mobile */}
        <aside
          className={cn(
            'lg:sticky lg:top-[calc(theme(spacing.header)+1.25rem)] lg:block lg:self-start',
            filtersOpen ? 'block' : 'hidden'
          )}
        >
          <div className='flex flex-col gap-4 rounded-card bg-surface p-4 ring-1 ring-inset ring-line'>
            <div className='flex items-center justify-between'>
              <h2 className='text-sm font-bold text-fg'>{t('filter.filters')}</h2>
              {activeFilters.length > 0 && (
                <button
                  type='button'
                  className='text-xs font-semibold text-accent-text hover:underline'
                  onClick={clearAll}
                >
                  {t('common:actions.clearFilters')}
                </button>
              )}
            </div>

            <Field label={t('common:actions.search')}>
              {(aria) => (
                <form
                  className='flex gap-1.5'
                  onSubmit={(e) => {
                    e.preventDefault();
                    setFilter('search', keyword.trim());
                  }}
                >
                  <input
                    {...aria}
                    className='h-9 w-full rounded-lg bg-surface-2 px-3 text-sm text-fg ring-1 ring-inset ring-line transition-shadow placeholder:text-fg-subtle focus:bg-surface focus:ring-accent'
                    placeholder={t('searchPlaceholder')}
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                  />
                  <Button type='submit' size='sm' aria-label={t('search')}>
                    <FaMagnifyingGlass className='size-3.5' />
                  </Button>
                </form>
              )}
            </Field>

            <Field label={t('filter.location')}>
              {(aria) => (
                <Select
                  {...aria}
                  size='sm'
                  data-testid='filter-prefecture'
                  value={searchParams.get('prefecture') || ''}
                  onChange={(e) => setFilter('prefecture', e.target.value)}
                >
                  <option value=''>{t('filter.anyLocation')}</option>
                  {filters?.prefectures?.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </Select>
              )}
            </Field>

            <Field label={t('filter.japanese')}>
              {(aria) => (
                <Select
                  {...aria}
                  size='sm'
                  data-testid='filter-japanese'
                  value={searchParams.get('japanese') || ''}
                  onChange={(e) => setFilter('japanese', e.target.value)}
                >
                  <option value=''>{t('filter.anyJapanese')}</option>
                  {filters?.japaneseLevels?.map((lv) => (
                    <option key={lv} value={lv}>
                      {japaneseLevelLabel(t, lv)}
                    </option>
                  ))}
                </Select>
              )}
            </Field>

            <Field label={t('filter.salary')}>
              {(aria) => (
                <Select
                  {...aria}
                  size='sm'
                  data-testid='filter-salary'
                  value={searchParams.get('salaryMin') || ''}
                  onChange={(e) => setFilter('salaryMin', e.target.value)}
                >
                  <option value=''>{t('filter.anySalary')}</option>
                  <option value='3000000'>{t('filter.from300')}</option>
                  <option value='5000000'>{t('filter.from500')}</option>
                  <option value='8000000'>{t('filter.from800')}</option>
                </Select>
              )}
            </Field>

            <label className='flex cursor-pointer items-center gap-2.5 rounded-lg bg-surface-2 px-3 py-2 text-sm font-medium text-fg'>
              <input
                type='checkbox'
                className='size-4 accent-asagi-600'
                checked={searchParams.get('remote') === 'true'}
                onChange={(e) => setFilter('remote', e.target.checked ? 'true' : '')}
              />
              {t('filter.remoteOnly')}
            </label>
          </div>
        </aside>

        <section>
          {activeFilters.length > 0 && (
            <div className='mb-4 flex flex-wrap items-center gap-2'>
              <span className='text-xs font-semibold text-fg-subtle'>
                {t('filter.activeFilters')}
              </span>
              {activeFilters.map(([key, value]) => (
                <button
                  key={key}
                  type='button'
                  className='transition-opacity hover:opacity-75'
                  onClick={() => {
                    if (key === 'search') setKeyword('');
                    setFilter(key, '');
                  }}
                >
                  <Badge tone='accent' icon={FaXmark}>
                    {labelOfFilter(key, value)}
                  </Badge>
                </button>
              ))}
            </div>
          )}

          {isLoading || isFetching ? (
            <SkeletonList count={4} item={JobSkeleton} />
          ) : data?.jobs?.length ? (
            <>
              <div className='grid grid-cols-1 gap-4 2xl:grid-cols-2'>{renderedJobs}</div>
              <Pagination curPage={data?.curPage || 1} totalPage={data?.totalPage || 1} />
            </>
          ) : (
            <EmptyState
              icon={FaBriefcase}
              title={t('empty')}
              description={t('emptyHint')}
              action={
                activeFilters.length > 0 && (
                  <Button variant='outline' size='sm' onClick={clearAll}>
                    {t('common:actions.clearFilters')}
                  </Button>
                )
              }
            />
          )}
        </section>
      </div>
    </Page>
  );
}

export default RecruitmentLayout;
