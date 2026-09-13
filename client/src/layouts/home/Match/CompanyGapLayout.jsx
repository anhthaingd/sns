import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaArrowUpRightFromSquare } from 'react-icons/fa6';
import Page from '../../Page';
import Card from '../../../components/ui/Card';
import Avatar from '../../../components/ui/Avatar';
import Loading from '../../../components/ui/Loading';
import ScoreDial from '../../../components/ui/ScoreDial';
import {
  useGetCompanyAdviceQuery,
  useGetCompanyGapQuery,
} from '../../../services/redux/query/api/matchApi';
import GapList from './components/GapList';
import AdviceCard from '../../../components/ui/AdviceCard';
import useAdviceLang from '../../../hooks/useAdviceLang';
import MatchScore from './components/MatchScore';
import MatchError from './components/MatchError';
import { formatSalary } from '../../../services/utils/jobFormat';

/**
 * Chức năng 2 ở mức công ty — tổng hợp thiếu sót trên MỌI vị trí đang tuyển.
 *
 * Khác trang theo vị trí: ở đây trả lời "công ty này nói chung đòi những gì mà
 * mình chưa có", nên gộp và loại trùng thiếu sót của tất cả vị trí.
 */
function CompanyGapLayout() {
  const { t } = useTranslation(['match', 'job', 'error']);
  const { id } = useParams();
  const { data, isLoading, isError, error } = useGetCompanyGapQuery(id);

  const lang = useAdviceLang();
  const advice = useGetCompanyAdviceQuery({ id, lang }, { skip: isError });

  if (isLoading) return <Loading />;
  if (isError) {
    return (
      <MatchError
        error={error}
        fallbackKey='jobGap.loadFailed'
        to='/match'
        actionKey='backToList'
      />
    );
  }

  const { company, bestJob, bestMatch, positions, combinedGaps } = data;

  return (
    <Page rail={false}>
      <Card className='flex flex-col gap-4'>
        <div className='flex flex-wrap items-start justify-between gap-4'>
          <div className='flex min-w-0 items-center gap-3'>
            <Avatar
              src={company.logo_url}
              name={company.name}
              size='xl'
              className='rounded-xl'
            />
            <div className='min-w-0'>
              <h1 className='truncate text-xl font-bold text-fg sm:text-2xl'>
                {company.name}
              </h1>
              {company.website && (
                <a
                  href={company.website}
                  target='_blank'
                  rel='noreferrer'
                  className='mt-0.5 inline-flex items-center gap-1.5 text-sm text-accent-text hover:underline'
                >
                  <span className='truncate'>{company.website}</span>
                  <FaArrowUpRightFromSquare className='size-3 shrink-0' aria-hidden='true' />
                </a>
              )}
            </div>
          </div>
          <MatchScore match={bestMatch} size='lg' />
        </div>

        {company.description && (
          <p className='whitespace-pre-line text-sm leading-relaxed text-fg-muted'>
            {company.description}
          </p>
        )}
        {company.tech_stack?.length > 0 && (
          <p className='text-sm text-fg'>
            <span className='font-semibold text-fg-subtle'>{t('techStack')} </span>
            {company.tech_stack.join(', ')}
          </p>
        )}
      </Card>

      <section className='mt-6'>
        <h2 className='text-lg font-bold text-fg'>
          {t('companyGap.title', { name: company.name })}
        </h2>
        <p className='mb-4 mt-1 text-sm text-fg-muted'>
          {t('companyGap.summary', { count: positions.length })}{' '}
          <Link
            to={`/match/jobs/${bestJob._id}`}
            className='font-semibold text-accent-text hover:underline'
          >
            {bestJob.title}
          </Link>
        </p>
        <GapList gaps={combinedGaps} met={bestMatch.met} />
        <AdviceCard data={advice.data} isLoading={advice.isLoading} />
      </section>

      <section className='mt-8'>
        <h2 className='mb-3 text-lg font-bold text-fg'>{t('openPositions')}</h2>
        <ul className='flex flex-col gap-2'>
          {positions.map((p) => (
            <li key={p.job._id}>
              <Link
                to={`/match/jobs/${p.job._id}`}
                className='flex items-center gap-4 rounded-card bg-surface p-3 ring-1 ring-inset ring-line transition-all duration-150 hover:shadow-card-hover hover:ring-accent/40'
              >
                <div className='min-w-0 flex-1'>
                  <p className='truncate text-sm font-semibold text-fg'>
                    {p.job.title}
                  </p>
                  <p className='tnum truncate text-sm text-fg-muted'>
                    {formatSalary(t, p.job.salary_min, p.job.salary_max)}
                    {p.job.prefecture ? ` · ${p.job.prefecture}` : ''}
                  </p>
                </div>
                <ScoreDial value={p.match.score} size='sm' label={t('score.label')} />
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </Page>
  );
}

export default CompanyGapLayout;
