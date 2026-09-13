import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCheck, FaArrowTrendUp, FaLightbulb } from 'react-icons/fa6';
import Page from '../../Page';
import Card from '../../../components/ui/Card';
import Loading from '../../../components/ui/Loading';
import SectionHeading from '../../../components/ui/SectionHeading';
import MatchError from './components/MatchError';
import {
  useGetWhatIfAdviceQuery,
  useGetWhatIfQuery,
  useSimulateWhatIfMutation,
} from '../../../services/redux/query/api/matchApi';
import AdviceCard from '../../../components/ui/AdviceCard';
import useAdviceLang from '../../../hooks/useAdviceLang';
import { formatSalary } from '../../../services/utils/jobFormat';
import cn from '../../../services/utils/cn';

// Khoá nhận diện một phương án — dùng cho cả `key` của React lẫn tập đã chọn.
const actionKey = (a) => `${a.kind}:${a.value}`;

function WhatIfLayout() {
  const { t } = useTranslation(['whatif', 'job', 'common']);
  const { data, isSuccess, isLoading, isError, error } = useGetWhatIfQuery();

  const lang = useAdviceLang();
  const advice = useGetWhatIfAdviceQuery({ lang }, { skip: isError });
  const [simulate, { data: combined }] = useSimulateWhatIfMutation();
  const [selected, setSelected] = useState([]);

  const toggle = useCallback(
    (action) => {
      const key = actionKey(action);
      const next = selected.some((a) => actionKey(a) === key)
        ? selected.filter((a) => actionKey(a) !== key)
        : [...selected, { kind: action.kind, value: action.value }];
      setSelected(next);
      if (next.length) simulate(next);
    },
    [selected, simulate]
  );

  // Nhãn của một phương án. Bậc ngôn ngữ là MÃ THÔ ("business") nên phải tra
  // bản dịch; kỹ năng là tên riêng ("AWS") nên giữ nguyên.
  const actionLabel = useCallback(
    (a) =>
      t(`action.${a.kind}`, {
        value:
          a.kind === 'japanese' || a.kind === 'english'
            ? t(`job:level.${a.value}`, { defaultValue: a.value })
            : a.value,
      }),
    [t]
  );

  const rows = useMemo(
    () =>
      (data?.suggestions || []).map((s) => {
        const chosen = selected.some((a) => actionKey(a) === actionKey(s));
        const helps = s.deltaJobs > 0;
        return (
          <li key={actionKey(s)}>
            <button
              type='button'
              data-testid='whatif-option'
              aria-pressed={chosen}
              onClick={() => toggle(s)}
              className={cn(
                'w-full rounded-card p-4 text-left ring-1 ring-inset transition-all duration-150',
                chosen
                  ? 'bg-accent-soft ring-2 ring-accent'
                  : 'bg-surface ring-line hover:ring-line-strong'
              )}
            >
              <span className='flex items-start justify-between gap-3'>
                <span className='flex min-w-0 items-center gap-2.5'>
                  <span
                    className={cn(
                      'flex size-5 shrink-0 items-center justify-center rounded-md ring-1 ring-inset transition-colors',
                      chosen
                        ? 'bg-accent text-accent-on ring-accent'
                        : 'bg-surface-2 text-transparent ring-line-strong'
                    )}
                    aria-hidden='true'
                  >
                    <FaCheck className='size-2.5' />
                  </span>
                  <span className='truncate font-semibold text-fg'>
                    {actionLabel(s)}
                  </span>
                </span>
                <span
                  data-testid='whatif-delta'
                  className={cn(
                    'tnum shrink-0 text-sm font-bold',
                    helps ? 'text-success-text' : 'text-fg-subtle'
                  )}
                >
                  {helps ? (
                    <span className='inline-flex items-center gap-1'>
                      <FaArrowTrendUp className='size-3' aria-hidden='true' />
                      {t('opens', { count: s.deltaJobs })}
                    </span>
                  ) : (
                    t('noBenefit')
                  )}
                </span>
              </span>
              <span className='mt-1.5 block pl-[1.875rem] text-sm text-fg-subtle'>
                {s.openedSalaryMedian
                  ? t('openedSalary', {
                      salary: formatSalary(t, s.openedSalaryMedian, s.openedSalaryMedian),
                      sample: s.openedSalarySample,
                    })
                  : t('openedSalaryUnknown')}
              </span>
            </button>
          </li>
        );
      }),
    // `t` trong mảng phụ thuộc: đổi ngôn ngữ -> react-i18next trả `t` mới;
    // thiếu nó thì danh sách đã memo hoá giữ chữ của ngôn ngữ cũ.
    [data, selected, t, actionLabel, toggle]
  );

  if (isLoading) return <Loading />;
  if (isError) return <MatchError error={error} />;

  const sumOfParts =
    combined && combined.baseline.qualifiedJobs + combined.sumOfIndividualDeltas;

  return (
    <Page rail={false}>
      <SectionHeading
        title={t('title')}
        description={isSuccess ? t('intro', { total: data.totalJobs }) : undefined}
      />

      {isSuccess && (
        // Con số xuất phát là mốc để so mọi thay đổi bên dưới, nên cho nó một
        // ô riêng cỡ lớn thay vì một dòng in đậm lẫn trong đoạn văn.
        <Card className='mt-5 flex items-center gap-4 bg-brand-soft ring-brand/20'>
          <span className='flex size-11 shrink-0 items-center justify-center rounded-full bg-brand text-brand-on'>
            <FaLightbulb className='size-5' aria-hidden='true' />
          </span>
          <p className='tnum text-sm font-semibold text-brand-text' data-testid='whatif-baseline'>
            {/* Lồng bản dịch chứ không ghép hai câu bằng dấu cách trong JSX:
                tiếng Nhật không đặt dấu cách trước 「（」, nên "94件 （65社）"
                đọc sai. Lồng vào thì mỗi ngôn ngữ tự quyết định dấu nối, và
                cả hai chỗ đếm đều giữ được dạng số ít/số nhiều riêng. */}
            {t('baseline', {
              count: data.baseline.qualifiedJobs,
              companies: t('companies', { count: data.baseline.qualifiedCompanies }),
            })}
          </p>
        </Card>
      )}

      <ul className='mt-6 flex flex-col gap-2'>{rows}</ul>

      {/* Kết quả kết hợp dính ở đáy màn hình: danh sách phương án dài, mà con
          số này phải nhìn thấy được ngay lúc đang tick chọn. */}
      <Card className='sticky bottom-20 mt-6 shadow-pop lg:bottom-4'>
        <h2 className='text-base font-bold text-fg'>{t('combined.title')}</h2>
        {selected.length === 0 ? (
          <p className='mt-1 text-sm text-fg-muted'>{t('combined.empty')}</p>
        ) : (
          combined && (
            <>
              <p
                className='tnum mt-1 font-display text-2xl font-black text-accent-text'
                data-testid='whatif-combined'
              >
                {t('combined.result', { count: combined.combined.qualifiedJobs })}
              </p>
              {/* Cả hai chiều đều xảy ra được: kết hợp có thể NHIỀU hơn tổng
                  lẻ (tin đòi cùng lúc nhiều điều kiện) hoặc ÍT hơn (một tin
                  được mở bởi cả hai mục). Nói đúng chiều đang xảy ra. */}
              {combined.combined.qualifiedJobs > sumOfParts && (
                <p className='mt-1 text-sm text-fg-subtle'>
                  {t('combined.more', { sum: sumOfParts })}
                </p>
              )}
              {combined.combined.qualifiedJobs < sumOfParts && (
                <p className='mt-1 text-sm text-fg-subtle'>
                  {t('combined.fewer', { sum: sumOfParts })}
                </p>
              )}
            </>
          )
        )}
      </Card>

      <AdviceCard data={advice.data} isLoading={advice.isLoading} />

      <p className='mt-4 text-xs leading-relaxed text-fg-subtle'>{t('disclaimer')}</p>
    </Page>
  );
}

export default WhatIfLayout;
