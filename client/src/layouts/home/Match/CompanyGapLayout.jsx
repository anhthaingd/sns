import { Link, useParams } from 'react-router-dom';
import Page from '../../Page';
import Loading from '../../../components/ui/Loading';
import { useGetCompanyGapQuery } from '../../../services/redux/query/api/matchApi';
import GapList from './components/GapList';
import MatchScore from './components/MatchScore';
import { formatSalary } from '../Recruitment/components/JobCard';

/**
 * Chức năng 2 ở mức công ty — tổng hợp thiếu sót trên MỌI vị trí đang tuyển.
 *
 * Khác trang theo vị trí: ở đây trả lời "công ty này nói chung đòi những gì mà
 * mình chưa có", nên gộp và loại trùng thiếu sót của tất cả vị trí.
 */
function CompanyGapLayout() {
  const { id } = useParams();
  const { data, isLoading, isError, error } = useGetCompanyGapQuery(id);

  if (isLoading) return <Loading />;
  if (isError) {
    return (
      <Page>
        <section className='p-8 rounded-lg border border-neutral-300 dark:border-neutral-700 flex flex-col items-center gap-4'>
          <p className='font-bold'>{error?.data?.message || 'Không tải được dữ liệu.'}</p>
          <Link to='/match' className='px-4 py-2 rounded bg-blue-500 text-neutral-50'>
            Về danh sách gợi ý
          </Link>
        </section>
      </Page>
    );
  }

  const { company, bestJob, bestMatch, positions, combinedGaps } = data;

  return (
    <Page>
      <section className='mb-6 flex flex-col gap-3'>
        <div className='flex justify-between items-start gap-4 flex-wrap'>
          <div className='flex gap-3 items-center'>
            {company.logo_url && (
              <img className='size-14 rounded object-contain bg-white' src={company.logo_url} alt='' />
            )}
            <div>
              <h1 className='text-2xl font-bold'>{company.name}</h1>
              {company.website && (
                <a
                  href={company.website}
                  target='_blank'
                  rel='noreferrer'
                  className='text-sm text-blue-600 dark:text-blue-400 hover:underline'
                >
                  {company.website}
                </a>
              )}
            </div>
          </div>
          <MatchScore match={bestMatch} />
        </div>

        {company.description && (
          <p className='text-sm opacity-80 whitespace-pre-line'>{company.description}</p>
        )}
        {company.tech_stack?.length > 0 && (
          <p className='text-sm'>
            <span className='opacity-70'>Công nghệ công ty dùng: </span>
            {company.tech_stack.join(', ')}
          </p>
        )}
      </section>

      <section className='mb-6'>
        <h2 className='text-lg font-bold mb-3'>Bạn còn thiếu gì để vào {company.name}</h2>
        <p className='text-sm opacity-70 mb-3'>
          Tổng hợp từ {positions.length} vị trí đang tuyển. Vị trí khớp nhất hiện tại:{' '}
          <Link to={`/match/jobs/${bestJob._id}`} className='text-blue-600 dark:text-blue-400 hover:underline'>
            {bestJob.title}
          </Link>
        </p>
        <GapList gaps={combinedGaps} met={bestMatch.met} />
      </section>

      <section>
        <h2 className='text-lg font-bold mb-3'>Các vị trí đang tuyển</h2>
        <ul className='flex flex-col gap-2'>
          {positions.map((p) => (
            <li
              key={p.job._id}
              className='p-3 rounded border border-neutral-300 dark:border-neutral-600 flex justify-between items-center gap-4 flex-wrap'
            >
              <div>
                <Link
                  to={`/match/jobs/${p.job._id}`}
                  className='font-medium hover:text-blue-500'
                >
                  {p.job.title}
                </Link>
                <p className='text-sm opacity-70'>
                  {formatSalary(p.job.salary_min, p.job.salary_max)}
                  {p.job.prefecture ? ` · ${p.job.prefecture}` : ''}
                </p>
              </div>
              <span className='px-3 py-1 rounded-full font-bold bg-neutral-200 dark:bg-neutral-700'>
                {p.match.score}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </Page>
  );
}

export default CompanyGapLayout;
