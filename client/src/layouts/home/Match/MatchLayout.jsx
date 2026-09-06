import { useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import Page from '../../Page';
import Pagination from '../../../components/ui/Pagination';
import Loading from '../../../components/ui/Loading';
import NotFoundItem from '../../../components/ui/NotFoundItem';
import { useGetMatchedCompaniesQuery } from '../../../services/redux/query/api/matchApi';
import MatchScore from './components/MatchScore';
import { formatSalary } from '../../../services/utils/jobFormat';
import { gapText } from '../../../services/utils/matchText';
import { useTranslation } from 'react-i18next';
import { serverMessage } from '../../../services/utils/serverMessage';

/**
 * Chức năng 1 — "CV của tôi hợp với công ty nào".
 *
 * Danh sách gom theo CÔNG TY (mỗi công ty lấy vị trí khớp nhất) vì người dùng
 * hỏi "công ty nào", không phải "20 vị trí của cùng một công ty".
 */
function MatchLayout() {
  const { t } = useTranslation(['match', 'job', 'error']);
  const [searchParams, setSearchParams] = useSearchParams();
  const qualifiedOnly = searchParams.get('qualifiedOnly') === 'true';

  const query = useMemo(() => {
    const params = new URLSearchParams();
    params.set('page', searchParams.get('page') || 1);
    if (qualifiedOnly) params.set('qualifiedOnly', 'true');
    return params.toString();
  }, [searchParams, qualifiedOnly]);

  const { data, isLoading, isError, error } = useGetMatchedCompaniesQuery(query);

  if (isLoading) return <Loading />;

  // Chưa có CV thì backend trả 404 kèm hướng dẫn — dẫn thẳng người dùng sang
  // trang tạo CV thay vì hiện lỗi cụt lủn.
  if (isError) {
    return (
      <Page>
        <section className='p-8 rounded-lg border border-neutral-300 dark:border-neutral-700 flex flex-col items-center gap-4'>
          <p className='font-bold'>
            {serverMessage(t, error?.data, 'loadFailed')}
          </p>
          <Link to='/resume' className='px-4 py-2 rounded bg-blue-500 text-neutral-50'>
            {t('createResume')}
          </Link>
        </section>
      </Page>
    );
  }

  return (
    <Page>
      <section className='mb-6 flex flex-col gap-3'>
        <h1 className='text-2xl font-bold'>{t('title')}</h1>
        <p className='text-sm opacity-70'>
          {t('subtitle', { count: data?.totalCompanies ?? 0 })}
        </p>

        {!data?.semanticAvailable && (
          // Nói thẳng khi phần xếp hạng ngữ nghĩa đang tắt, thay vì để giao diện
          // tỏ ra thông minh hơn thực tế.
          <p className='text-sm p-3 rounded bg-amber-50 dark:bg-amber-950 border-l-4 border-amber-500'>
            {t('ruleOnlyNotice')}
          </p>
        )}

        <label className='flex items-center gap-2 text-sm self-start'>
          <input
            type='checkbox'
            checked={qualifiedOnly}
            onChange={(e) => {
              // `createQueryString` bỏ qua giá trị rỗng nên bỏ tick sẽ không xoá
              // được tham số; dựng URLSearchParams thẳng cho chắc.
              const next = new URLSearchParams(searchParams.toString());
              if (e.target.checked) next.set('qualifiedOnly', 'true');
              else next.delete('qualifiedOnly');
              next.set('page', '1');
              setSearchParams(next);
            }}
          />
          {t('qualifiedOnly')}
        </label>
      </section>

      {data?.matches?.length ? (
        <>
          <section className='flex flex-col gap-4'>
            {data.matches.map((m) => (
              <article
                key={m.company._id || m.company.name}
                className='p-4 rounded-lg border border-neutral-300 dark:border-neutral-600 bg-neutral-50 dark:bg-neutral-800 flex flex-col gap-3'
              >
                <div className='flex justify-between items-start gap-4 flex-wrap'>
                  <div className='flex gap-3 items-center'>
                    {m.company.logo_url && (
                      <img
                        className='size-12 rounded object-contain bg-white'
                        src={m.company.logo_url}
                        alt=''
                        {...{ fetchPriority: 'low' }}
                      />
                    )}
                    <div>
                      <h2 className='font-bold text-lg'>{m.company.name}</h2>
                      <p className='text-sm opacity-70'>
                        {m.company.location || t('unknownLocation')}
                        {m.company.job_count
                          ? ` · ${t('positionCount', {
                              count: m.company.job_count,
                            })}`
                          : ''}
                      </p>
                    </div>
                  </div>
                  <MatchScore match={m.match} />
                </div>

                {m.company.description && (
                  <p className='text-sm opacity-80 line-clamp-2'>{m.company.description}</p>
                )}

                <div className='p-3 rounded bg-neutral-100 dark:bg-neutral-700 text-sm'>
                  <p className='font-medium'>
                    {t('bestJob')} {m.bestJob.title}
                  </p>
                  <p className='opacity-70'>
                    {formatSalary(t, m.bestJob.salary_min, m.bestJob.salary_max)}
                    {m.bestJob.prefecture ? ` · ${m.bestJob.prefecture}` : ''}
                  </p>
                </div>

                {m.match.gaps.length > 0 && (
                  <p className='text-sm'>
                    <span className='opacity-70'>{t('missingPrefix')} </span>
                    {gapText(t, m.match.gaps[0])}
                    {m.match.gaps.length > 1 &&
                      ` ${t('moreGaps', { count: m.match.gaps.length - 1 })}`}
                  </p>
                )}

                <div className='flex gap-4 text-sm'>
                  {m.company._id && (
                    <Link
                      to={`/match/companies/${m.company._id}`}
                      className='text-blue-600 dark:text-blue-400 hover:underline'
                    >
                      {t('companyGapLink')}
                    </Link>
                  )}
                  <Link
                    to={`/match/jobs/${m.bestJob._id}`}
                    className='text-blue-600 dark:text-blue-400 hover:underline'
                  >
                    {t('jobDetailLink')}
                  </Link>
                </div>
              </article>
            ))}
          </section>
          <Pagination curPage={data?.curPage || 1} totalPage={data?.totalPage || 1} />
        </>
      ) : (
        <NotFoundItem message={t('empty')} />
      )}
    </Page>
  );
}

export default MatchLayout;
