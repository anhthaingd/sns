import { useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import Page from '../../Page';
import Pagination from '../../../components/ui/Pagination';
import Loading from '../../../components/ui/Loading';
import NotFoundItem from '../../../components/ui/NotFoundItem';
import { useGetMatchedCompaniesQuery } from '../../../services/redux/query/api/matchApi';
import MatchScore from './components/MatchScore';
import { formatSalary } from '../Recruitment/components/JobCard';

/**
 * Chức năng 1 — "CV của tôi hợp với công ty nào".
 *
 * Danh sách gom theo CÔNG TY (mỗi công ty lấy vị trí khớp nhất) vì người dùng
 * hỏi "công ty nào", không phải "20 vị trí của cùng một công ty".
 */
function MatchLayout() {
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
          <p className='font-bold'>{error?.data?.message || 'Không tải được gợi ý.'}</p>
          <Link to='/resume' className='px-4 py-2 rounded bg-blue-500 text-neutral-50'>
            Tạo CV ngay
          </Link>
        </section>
      </Page>
    );
  }

  return (
    <Page>
      <section className='mb-6 flex flex-col gap-3'>
        <h1 className='text-2xl font-bold'>Công ty phù hợp với bạn</h1>
        <p className='text-sm opacity-70'>
          Xếp hạng {data?.totalCompanies ?? 0} công ty dựa trên CV của bạn: mức độ liên quan về
          ngành nghề cộng với mức đáp ứng các yêu cầu cứng (tiếng Nhật, kinh nghiệm, kỹ năng).
        </p>

        {!data?.semanticAvailable && (
          // Nói thẳng khi phần xếp hạng ngữ nghĩa đang tắt, thay vì để giao diện
          // tỏ ra thông minh hơn thực tế.
          <p className='text-sm p-3 rounded bg-amber-50 dark:bg-amber-950 border-l-4 border-amber-500'>
            Đang xếp hạng bằng luật (tiếng Nhật, kinh nghiệm, kỹ năng). Phần so khớp theo ngữ
            nghĩa chưa sẵn sàng — kết quả vẫn dùng được, chỉ kém tinh tế hơn.
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
          Chỉ hiện công ty tôi đã đủ điều kiện
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
                        {m.company.location || 'Chưa rõ địa điểm'}
                        {m.company.job_count ? ` · ${m.company.job_count} vị trí` : ''}
                      </p>
                    </div>
                  </div>
                  <MatchScore match={m.match} />
                </div>

                {m.company.description && (
                  <p className='text-sm opacity-80 line-clamp-2'>{m.company.description}</p>
                )}

                <div className='p-3 rounded bg-neutral-100 dark:bg-neutral-700 text-sm'>
                  <p className='font-medium'>Vị trí khớp nhất: {m.bestJob.title}</p>
                  <p className='opacity-70'>
                    {formatSalary(m.bestJob.salary_min, m.bestJob.salary_max)}
                    {m.bestJob.prefecture ? ` · ${m.bestJob.prefecture}` : ''}
                  </p>
                </div>

                {m.match.gaps.length > 0 && (
                  <p className='text-sm'>
                    <span className='opacity-70'>Còn thiếu: </span>
                    {m.match.gaps[0].message}
                    {m.match.gaps.length > 1 && ` (và ${m.match.gaps.length - 1} điểm khác)`}
                  </p>
                )}

                <div className='flex gap-4 text-sm'>
                  {m.company._id && (
                    <Link
                      to={`/match/companies/${m.company._id}`}
                      className='text-blue-600 dark:text-blue-400 hover:underline'
                    >
                      Tôi còn thiếu gì để vào công ty này →
                    </Link>
                  )}
                  <Link
                    to={`/match/jobs/${m.bestJob._id}`}
                    className='text-blue-600 dark:text-blue-400 hover:underline'
                  >
                    Chi tiết vị trí →
                  </Link>
                </div>
              </article>
            ))}
          </section>
          <Pagination curPage={data?.curPage || 1} totalPage={data?.totalPage || 1} />
        </>
      ) : (
        <NotFoundItem message='Chưa có công ty nào phù hợp. Thử bỏ bộ lọc "đã đủ điều kiện".' />
      )}
    </Page>
  );
}

export default MatchLayout;
