import React from 'react';
import { Link, useParams } from 'react-router-dom';
import Page from '../../Page';
import Loading from '../../../components/ui/Loading';
import { useGetJobGapQuery } from '../../../services/redux/query/usersQuery';
import GapList from './components/GapList';
import MatchScore from './components/MatchScore';
import { LEVEL_LABELS, formatSalary } from '../Recruitment/components/JobCard';

/** Chức năng 2 — "tôi còn thiếu gì để vào vị trí này". */
function JobGapLayout() {
  const { id } = useParams();
  const { data, isLoading, isError, error } = useGetJobGapQuery(id);

  if (isLoading) return <Loading />;
  if (isError) {
    return (
      <Page>
        <section className='p-8 rounded-lg border border-neutral-300 dark:border-neutral-700 flex flex-col items-center gap-4'>
          <p className='font-bold'>{error?.data?.message || 'Không tải được dữ liệu.'}</p>
          <Link to='/resume' className='px-4 py-2 rounded bg-blue-500 text-neutral-50'>
            Tạo CV ngay
          </Link>
        </section>
      </Page>
    );
  }

  const { job, company, match, qualified } = data;

  return (
    <Page>
      <section className='mb-6 flex flex-col gap-3'>
        <div className='flex justify-between items-start gap-4 flex-wrap'>
          <div>
            <h1 className='text-2xl font-bold'>{job.title}</h1>
            <p className='opacity-70'>
              {company?.name || job.company_name}
              {job.location ? ` · ${job.location}` : ''}
            </p>
          </div>
          <MatchScore match={match} />
        </div>

        <div
          className={`p-3 rounded border-l-4 ${
            qualified
              ? 'border-green-500 bg-green-50 dark:bg-green-950'
              : 'border-rose-500 bg-rose-50 dark:bg-rose-950'
          }`}
        >
          <p className='font-medium'>
            {qualified
              ? 'Bạn đã đáp ứng mọi điều kiện bắt buộc của vị trí này.'
              : 'Còn điều kiện bắt buộc chưa đạt — xem danh sách bên dưới.'}
          </p>
        </div>

        <div className='flex flex-wrap gap-x-6 gap-y-1 text-sm opacity-80'>
          <span>Lương: {formatSalary(job.salary_min, job.salary_max)}</span>
          {job.required_japanese && (
            <span>Tiếng Nhật: {LEVEL_LABELS[job.required_japanese] || job.required_japanese}</span>
          )}
          {job.min_years !== null && job.min_years !== undefined && (
            <span>Kinh nghiệm: {job.min_years} năm</span>
          )}
          {job.employment_type && <span>Hình thức: {job.employment_type}</span>}
        </div>

        <a
          href={job.url}
          target='_blank'
          rel='noreferrer'
          className='self-start text-sm text-blue-600 dark:text-blue-400 hover:underline'
        >
          Mở tin gốc trên {job.source} →
        </a>
      </section>

      <GapList gaps={match.gaps} met={match.met} />

      {company?.description && (
        <section className='mt-6 p-4 rounded-lg border border-neutral-300 dark:border-neutral-600'>
          <h3 className='font-bold mb-2'>Về {company.name}</h3>
          <p className='text-sm opacity-80 whitespace-pre-line'>{company.description}</p>
          {company.tech_stack?.length > 0 && (
            <p className='mt-2 text-sm'>
              <span className='opacity-70'>Công nghệ: </span>
              {company.tech_stack.join(', ')}
            </p>
          )}
        </section>
      )}
    </Page>
  );
}

export default JobGapLayout;
