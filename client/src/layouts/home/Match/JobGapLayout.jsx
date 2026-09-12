import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  FaCircleCheck,
  FaTriangleExclamation,
  FaArrowUpRightFromSquare,
} from 'react-icons/fa6';
import Page from '../../Page';
import Card from '../../../components/ui/Card';
import Loading from '../../../components/ui/Loading';
import LinkButton from '../../../components/ui/LinkButton';
import { useGetJobGapQuery } from '../../../services/redux/query/api/matchApi';
import GapList from './components/GapList';
import MatchScore from './components/MatchScore';
import MatchError from './components/MatchError';
import {
  experienceLabel,
  formatSalary,
  japaneseLevelLabel,
} from '../../../services/utils/jobFormat';
import cn from '../../../services/utils/cn';

/** Một ô số liệu trong bảng tóm tắt điều kiện của tin tuyển dụng. */
function Fact({ label, value }) {
  if (!value) return null;
  return (
    <div>
      <dt className='text-2xs font-semibold uppercase tracking-wider text-fg-subtle'>
        {label}
      </dt>
      <dd className='tnum mt-0.5 text-sm font-semibold text-fg'>{value}</dd>
    </div>
  );
}

/** Chức năng 2 — "tôi còn thiếu gì để vào vị trí này". */
function JobGapLayout() {
  const { t } = useTranslation(['match', 'job', 'error']);
  const { id } = useParams();
  const { data, isLoading, isError, error } = useGetJobGapQuery(id);

  if (isLoading) return <Loading />;
  if (isError) return <MatchError error={error} fallbackKey='jobGap.loadFailed' />;

  const { job, company, match, qualified } = data;

  return (
    <Page rail={false}>
      <Card className='flex flex-col gap-5'>
        <div className='flex flex-wrap items-start justify-between gap-4'>
          <div className='min-w-0'>
            <h1 className='text-xl font-bold leading-snug text-fg sm:text-2xl'>
              {job.title}
            </h1>
            <p className='mt-1 text-sm text-fg-muted'>
              {company?.name || job.company_name}
              {job.location ? ` · ${job.location}` : ''}
            </p>
          </div>
          <MatchScore match={match} size='lg' />
        </div>

        {/* Câu trả lời quan trọng nhất của trang này — nộp được hay chưa — đặt
            ngay dưới tiêu đề, có màu và biểu tượng riêng. */}
        <p
          className={cn(
            'flex items-center gap-2.5 rounded-lg border-l-[3px] p-3 text-sm font-semibold',
            qualified
              ? 'border-success bg-success-soft text-success-text'
              : 'border-danger bg-danger-soft text-danger-text'
          )}
        >
          {qualified ? (
            <FaCircleCheck className='size-4 shrink-0' aria-hidden='true' />
          ) : (
            <FaTriangleExclamation className='size-4 shrink-0' aria-hidden='true' />
          )}
          {qualified ? t('jobGap.qualified') : t('jobGap.notQualified')}
        </p>

        <dl className='grid grid-cols-2 gap-4 rounded-lg bg-surface-2 p-4 sm:grid-cols-4'>
          <Fact
            label={t('job:salary.label')}
            value={formatSalary(t, job.salary_min, job.salary_max)}
          />
          <Fact
            label={t('job:japaneseLabel')}
            value={
              job.required_japanese && japaneseLevelLabel(t, job.required_japanese)
            }
          />
          <Fact
            label={t('job:experience.label')}
            value={
              job.min_years !== null && job.min_years !== undefined
                ? experienceLabel(t, job.min_years)
                : null
            }
          />
          <Fact label={t('jobGap.employmentType')} value={job.employment_type} />
        </dl>

        <LinkButton
          href={job.url}
          external
          variant='outline'
          size='sm'
          iconRight={FaArrowUpRightFromSquare}
          className='self-start'
        >
          {t('jobGap.openOriginal', { source: job.source })}
        </LinkButton>
      </Card>

      <section className='mt-6'>
        <GapList gaps={match.gaps} met={match.met} />
      </section>

      {company?.description && (
        <Card className='mt-6'>
          <h2 className='text-base font-bold text-fg'>
            {t('jobGap.aboutCompany', { name: company.name })}
          </h2>
          <p className='mt-2 whitespace-pre-line text-sm leading-relaxed text-fg-muted'>
            {company.description}
          </p>
          {company.tech_stack?.length > 0 && (
            <p className='mt-3 text-sm text-fg'>
              <span className='font-semibold text-fg-subtle'>{t('jobTech')} </span>
              {company.tech_stack.join(', ')}
            </p>
          )}
        </Card>
      )}
    </Page>
  );
}

export default JobGapLayout;
