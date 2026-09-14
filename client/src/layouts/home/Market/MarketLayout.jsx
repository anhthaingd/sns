import { useTranslation } from 'react-i18next';
import { FaChartColumn } from 'react-icons/fa6';
import Page from '../../Page';
import Card from '../../../components/ui/Card';
import Loading from '../../../components/ui/Loading';
import EmptyState from '../../../components/ui/EmptyState';
import SectionHeading from '../../../components/ui/SectionHeading';
import BarChart from '../../../components/ui/BarChart';
import { serverMessage } from '../../../services/utils/serverMessage';
import {
  useGetJobMarketQuery,
  useGetMarketAdviceQuery,
} from '../../../services/redux/query/api/jobsApi';
import AdviceCard from '../../../components/ui/AdviceCard';
import useAdviceLang from '../../../hooks/useAdviceLang';
import { formatSalary } from '../../../services/utils/jobFormat';

const OTHER = '__other__';

/** Một khối biểu đồ có tiêu đề và phần chú thích tuỳ chọn bên dưới. */
function ChartSection({ title, children, note }) {
  return (
    <Card className='flex flex-col gap-3'>
      <h2 className='text-base font-bold text-fg'>{title}</h2>
      {children}
      {note && <p className='text-xs leading-relaxed text-fg-subtle'>{note}</p>}
    </Card>
  );
}

function MarketLayout() {
  const { t } = useTranslation(['market', 'job', 'common']);
  const { data, isSuccess, isLoading, isError, error } = useGetJobMarketQuery();

  // Trang này không nói về một người cụ thể, nên lời khuyên ở đây là đọc bảng
  // số thành nhận định thị trường.
  const lang = useAdviceLang();
  const advice = useGetMarketAdviceQuery({ lang }, { skip: isError });

  // Trung vị chỉ có khi nhóm đủ lớn — backend đã trả `null` dưới ngưỡng, ở đây
  // chỉ diễn đạt lại. Cỡ mẫu LUÔN hiện, kể cả khi không có trung vị.
  const caption = (row) =>
    `${t('jobs', { count: row.jobs })} · ${
      row.salaryMedian
        ? t('median', {
            salary: formatSalary(t, row.salaryMedian, row.salaryMedian),
            sample: row.salarySample,
          })
        : t('medianUnknown', { sample: row.salarySample })
    }`;

  // Ba trạng thái khác nhau, ba câu khác nhau. Gộp chung thành "chưa có dữ
  // liệu, chạy ETL trước" là nói sai: lúc đang tải thì dữ liệu đang trên
  // đường về, còn lúc lỗi mạng thì chạy ETL không cứu được gì.
  if (isLoading) return <Loading />;
  if (isError) {
    return (
      <Page rail={false}>
        <EmptyState
          icon={FaChartColumn}
          title={serverMessage(t, error?.data, 'loadFailed')}
        />
      </Page>
    );
  }
  if (!isSuccess || data.totalJobs === 0) {
    return (
      <Page rail={false}>
        <EmptyState icon={FaChartColumn} title={t('empty')} />
      </Page>
    );
  }

  // Phần dư KHÔNG vẽ thành cột: tổng của nó (đo được: 200 lượt) lớn hơn kỹ
  // năng đứng đầu (109), nên đặt chung một thang sẽ bóp hết các cột thật.
  const namedSkills = data.skills.filter((s) => s.skill !== OTHER);
  const otherSkills = data.skills.find((s) => s.skill === OTHER);

  return (
    <Page rail={false}>
      <SectionHeading
        title={t('title')}
        description={t('intro', { total: data.totalJobs })}
      />
      <p className='mt-2 text-xs leading-relaxed text-fg-subtle'>
        {t('caveat', { min: data.minGroupSize })}
      </p>

      <div className='mt-6 flex flex-col gap-4'>
        <ChartSection
          title={t('skills.title')}
          note={
            otherSkills &&
            t('skills.other', {
              distinct: otherSkills.distinct,
              jobs: otherSkills.jobs,
            })
          }
        >
          <BarChart
            emptyLabel={t('empty')}
            rows={namedSkills.map((s) => ({
              label: s.skill,
              value: s.jobs,
              caption: caption(s),
            }))}
          />
        </ChartSection>

        <ChartSection title={t('japanese.title')} note={t('finding')}>
          <BarChart
            emptyLabel={t('empty')}
            rows={data.japanese.map((r) => ({
              label: r.level
                ? t(`job:level.${r.level}`, { defaultValue: r.level })
                : t('japanese.unstated'),
              value: r.jobs,
              caption: caption(r),
            }))}
          />
        </ChartSection>

        <ChartSection title={t('prefectures.title')}>
          <BarChart
            emptyLabel={t('empty')}
            rows={data.prefectures.map((r) => ({
              label: r.prefecture,
              value: r.jobs,
              caption: caption(r),
            }))}
          />
        </ChartSection>
      </div>

      <AdviceCard
          data={advice.data}
          isLoading={advice.isLoading}
          isFetching={advice.isFetching}
        />
    </Page>
  );
}

export default MarketLayout;
