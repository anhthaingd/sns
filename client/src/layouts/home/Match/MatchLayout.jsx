import { useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaCircleInfo, FaBuilding, FaArrowRight } from 'react-icons/fa6';
import Page from '../../Page';
import Pagination from '../../../components/ui/Pagination';
import EmptyState from '../../../components/ui/EmptyState';
import SectionHeading from '../../../components/ui/SectionHeading';
import Avatar from '../../../components/ui/Avatar';
import Card from '../../../components/ui/Card';
import { JobSkeleton, SkeletonList } from '../../../components/ui/Skeleton';
import {
  useGetMatchedCompaniesQuery,
  useGetOverviewAdviceQuery,
} from '../../../services/redux/query/api/matchApi';
import MatchScore from './components/MatchScore';
import AdviceCard from '../../../components/ui/AdviceCard';
import useAdviceLang from '../../../hooks/useAdviceLang';
import MatchError from './components/MatchError';
import { formatSalary } from '../../../services/utils/jobFormat';
import { gapText } from '../../../services/utils/matchText';

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

  // MỘT lời khuyên cho cả trang, không phải mỗi công ty một đoạn: mười lần gọi
  // cho một lần mở trang là hết hạn mức miễn phí trong một buổi demo, mà mười
  // đoạn văn thì cũng không ai đọc.
  const lang = useAdviceLang();
  const advice = useGetOverviewAdviceQuery(
    { page: Number(searchParams.get('page')) || 1, lang },
    { skip: !data?.matches?.length }
  );

  // Chưa có CV thì backend trả 404 kèm hướng dẫn — dẫn thẳng người dùng sang
  // trang tạo CV thay vì hiện lỗi cụt lủn.
  if (isError) return <MatchError error={error} />;

  return (
    <Page rail={false}>
      <SectionHeading
        title={t('title')}
        description={t('subtitle', { count: data?.totalCompanies ?? 0 })}
      />

      <div className='mt-4 flex flex-wrap items-center gap-4'>
        <label className='flex cursor-pointer items-center gap-2.5 rounded-lg bg-surface px-3 py-2 text-sm font-medium text-fg ring-1 ring-inset ring-line'>
          <input
            type='checkbox'
            className='size-4 accent-asagi-600'
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
      </div>

      {data && !data.semanticAvailable && (
        // Nói thẳng khi phần xếp hạng ngữ nghĩa đang tắt, thay vì để giao diện
        // tỏ ra thông minh hơn thực tế.
        <p className='mt-4 flex items-start gap-2.5 rounded-lg border-l-[3px] border-warning bg-warning-soft p-3 text-sm text-fg'>
          <FaCircleInfo className='mt-0.5 size-4 shrink-0 text-warning-text' aria-hidden='true' />
          {t('ruleOnlyNotice')}
        </p>
      )}

      <div className='mt-6'>
        {isLoading ? (
          <SkeletonList count={4} item={JobSkeleton} />
        ) : data?.matches?.length ? (
          <>
            <div className='flex flex-col gap-4'>
              {data.matches.map((m) => (
                <Card
                  as='article'
                  key={m.company._id || m.company.name}
                  className='flex flex-col gap-4'
                >
                  <div className='flex flex-wrap items-start justify-between gap-4'>
                    <div className='flex min-w-0 items-center gap-3'>
                      <Avatar
                        src={m.company.logo_url}
                        name={m.company.name}
                        size='xl'
                        className='rounded-xl'
                      />
                      <div className='min-w-0'>
                        <h2 className='truncate text-base font-bold text-fg'>
                          {m.company.name}
                        </h2>
                        <p className='truncate text-sm text-fg-muted'>
                          {m.company.location || t('unknownLocation')}
                          {m.company.job_count
                            ? ` · ${t('positionCount', { count: m.company.job_count })}`
                            : ''}
                        </p>
                      </div>
                    </div>
                    <MatchScore match={m.match} />
                  </div>

                  {m.company.description && (
                    <p className='line-clamp-2 text-sm leading-relaxed text-fg-muted'>
                      {m.company.description}
                    </p>
                  )}

                  <div className='rounded-lg bg-surface-2 p-3'>
                    <p className='text-2xs font-semibold uppercase tracking-wider text-fg-subtle'>
                      {t('bestJob')}
                    </p>
                    <p className='mt-1 text-sm font-semibold text-fg'>
                      {m.bestJob.title}
                    </p>
                    <p className='tnum mt-0.5 text-sm text-fg-muted'>
                      {formatSalary(t, m.bestJob.salary_min, m.bestJob.salary_max)}
                      {m.bestJob.prefecture ? ` · ${m.bestJob.prefecture}` : ''}
                    </p>
                  </div>

                  {m.match.gaps.length > 0 && (
                    <p className='rounded-lg border-l-[3px] border-warning bg-warning-soft p-3 text-sm text-fg'>
                      <span className='font-semibold'>{t('missingPrefix')} </span>
                      {gapText(t, m.match.gaps[0])}
                      {m.match.gaps.length > 1 &&
                        ` ${t('moreGaps', { count: m.match.gaps.length - 1 })}`}
                    </p>
                  )}

                  <div className='flex flex-wrap gap-x-5 gap-y-2 border-t border-line pt-3 text-sm font-semibold'>
                    {m.company._id && (
                      <Link
                        to={`/match/companies/${m.company._id}`}
                        className='group inline-flex items-center gap-1.5 text-accent-text'
                      >
                        {t('companyGapLink')}
                        <FaArrowRight
                          className='size-3 transition-transform group-hover:translate-x-0.5'
                          aria-hidden='true'
                        />
                      </Link>
                    )}
                    <Link
                      to={`/match/jobs/${m.bestJob._id}`}
                      className='group inline-flex items-center gap-1.5 text-fg-muted hover:text-fg'
                    >
                      {t('jobDetailLink')}
                      <FaArrowRight
                        className='size-3 transition-transform group-hover:translate-x-0.5'
                        aria-hidden='true'
                      />
                    </Link>
                  </div>
                </Card>
              ))}
            </div>
            <Pagination curPage={data?.curPage || 1} totalPage={data?.totalPage || 1} />
          </>
        ) : (
          <EmptyState icon={FaBuilding} title={t('empty')} />
        )}

        {data?.matches?.length > 0 && (
          <AdviceCard data={advice.data} isLoading={advice.isLoading} />
        )}
      </div>
    </Page>
  );
}

export default MatchLayout;
