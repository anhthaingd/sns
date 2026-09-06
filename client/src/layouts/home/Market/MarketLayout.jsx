import { useTranslation } from 'react-i18next';
import Page from '../../Page';
import BarChart from '../../../components/ui/BarChart';
import { useGetJobMarketQuery } from '../../../services/redux/query/api/jobsApi';
import { formatSalary } from '../../../services/utils/jobFormat';

const OTHER = '__other__';

function MarketLayout() {
  const { t } = useTranslation(['market', 'job', 'common']);
  const { data, isSuccess } = useGetJobMarketQuery();

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

  if (!isSuccess) {
    return (
      <Page>
        <p className='p-4'>{t('empty')}</p>
      </Page>
    );
  }

  // Phần dư KHÔNG vẽ thành cột: tổng của nó (đo được: 200 lượt) lớn hơn kỹ
  // năng đứng đầu (109), nên đặt chung một thang sẽ bóp hết các cột thật.
  const namedSkills = data.skills.filter((s) => s.skill !== OTHER);
  const otherSkills = data.skills.find((s) => s.skill === OTHER);

  return (
    <Page>
      <div className='border border-neutral-300 dark:border-neutral-700 rounded-lg p-4 flex flex-col gap-8'>
        <div className='flex flex-col gap-2'>
          <h1 className='text-xl md:text-2xl font-bold'>{t('title')}</h1>
          <p>{t('intro', { total: data.totalJobs })}</p>
          <p className='text-sm text-neutral-500'>
            {t('caveat', { min: data.minGroupSize })}
          </p>
        </div>

        <section className='flex flex-col gap-3'>
          <h2 className='text-lg font-bold'>{t('skills.title')}</h2>
          <BarChart
            emptyLabel={t('empty')}
            rows={namedSkills.map((s) => ({
              label: s.skill,
              value: s.jobs,
              caption: caption(s),
            }))}
          />
          {otherSkills && (
            <p className='text-sm text-neutral-500'>
              {t('skills.other', {
                distinct: otherSkills.distinct,
                jobs: otherSkills.jobs,
              })}
            </p>
          )}
        </section>

        <section className='flex flex-col gap-3'>
          <h2 className='text-lg font-bold'>{t('japanese.title')}</h2>
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
          <p className='text-sm'>{t('finding')}</p>
        </section>

        <section className='flex flex-col gap-3'>
          <h2 className='text-lg font-bold'>{t('prefectures.title')}</h2>
          <BarChart
            emptyLabel={t('empty')}
            rows={data.prefectures.map((r) => ({
              label: r.prefecture,
              value: r.jobs,
              caption: caption(r),
            }))}
          />
        </section>
      </div>
    </Page>
  );
}

export default MarketLayout;
