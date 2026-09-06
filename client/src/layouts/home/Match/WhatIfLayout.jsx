import { useCallback, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Page from '../../Page';
import Loading from '../../../components/ui/Loading';
import { serverMessage } from '../../../services/utils/serverMessage';
import {
  useGetWhatIfQuery,
  useSimulateWhatIfMutation,
} from '../../../services/redux/query/api/matchApi';
import { formatSalary } from '../../../services/utils/jobFormat';

// Khoá nhận diện một phương án — dùng cho cả `key` của React lẫn tập đã chọn.
const actionKey = (a) => `${a.kind}:${a.value}`;

function WhatIfLayout() {
  const { t } = useTranslation(['whatif', 'job', 'common']);
  const { data, isSuccess, isLoading, isError, error } = useGetWhatIfQuery();
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
        return (
          <li key={actionKey(s)}>
            <button
              type='button'
              data-testid='whatif-option'
              aria-pressed={chosen}
              onClick={() => toggle(s)}
              className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                chosen
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
                  : 'border-neutral-300 dark:border-neutral-700 hover:bg-neutral-100 dark:hover:bg-neutral-800'
              }`}
            >
              <span className='flex justify-between items-center gap-3'>
                <span className='font-bold'>{actionLabel(s)}</span>
                <span
                  data-testid='whatif-delta'
                  className={s.deltaJobs > 0 ? 'font-bold text-blue-600 dark:text-blue-400' : 'text-neutral-500'}
                >
                  {s.deltaJobs > 0 ? t('opens', { count: s.deltaJobs }) : t('noBenefit')}
                </span>
              </span>
              <span className='block text-sm text-neutral-500 mt-1'>
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

  // Hiện CÂU LỖI THẬT từ máy chủ chứ không viết cứng "bạn cần tạo CV": mất
  // mạng hay lỗi 500 cũng vào nhánh này, mà nói "bạn cần tạo CV" khi người ta
  // đã có CV thì họ đi tìm sai chỗ. Chưa có CV thì backend trả mã
  // `match.noResume` và câu chữ đúng tự hiện ra.
  if (isError) {
    return (
      <Page>
        <section className='p-8 rounded-lg border border-neutral-300 dark:border-neutral-700 flex flex-col items-center gap-4'>
          <p className='font-bold'>{serverMessage(t, error?.data, 'loadFailed')}</p>
          <Link to='/resume' className='px-4 py-2 rounded bg-blue-500 text-neutral-50'>
            {t('createResume')}
          </Link>
        </section>
      </Page>
    );
  }

  const sumOfParts =
    combined && combined.baseline.qualifiedJobs + combined.sumOfIndividualDeltas;

  return (
    <Page>
      <div className='border border-neutral-300 dark:border-neutral-700 rounded-lg p-4 flex flex-col gap-6'>
        <div className='flex flex-col gap-2'>
          <h1 className='text-xl md:text-2xl font-bold'>{t('title')}</h1>
          {isSuccess && (
            <>
              <p>{t('intro', { total: data.totalJobs })}</p>
              {/* Lồng bản dịch chứ không ghép hai câu bằng dấu cách trong JSX:
                  tiếng Nhật không đặt dấu cách trước 「（」, nên "94件 （65社）"
                  đọc sai. Lồng vào thì mỗi ngôn ngữ tự quyết định dấu nối, và
                  cả hai chỗ đếm đều giữ được dạng số ít/số nhiều riêng. */}
              <p className='font-bold' data-testid='whatif-baseline'>
                {t('baseline', {
                  count: data.baseline.qualifiedJobs,
                  companies: t('companies', {
                    count: data.baseline.qualifiedCompanies,
                  }),
                })}
              </p>
            </>
          )}
        </div>

        <ul className='flex flex-col gap-2'>{rows}</ul>

        <section className='border-t border-neutral-300 dark:border-neutral-700 pt-4 flex flex-col gap-2'>
          <h2 className='text-lg font-bold'>{t('combined.title')}</h2>
          {selected.length === 0 && <p>{t('combined.empty')}</p>}
          {selected.length > 0 && combined && (
            <>
              <p className='font-bold' data-testid='whatif-combined'>
                {t('combined.result', { count: combined.combined.qualifiedJobs })}
              </p>
              {/* Cả hai chiều đều xảy ra được: kết hợp có thể NHIỀU hơn tổng
                  lẻ (tin đòi cùng lúc nhiều điều kiện) hoặc ÍT hơn (một tin
                  được mở bởi cả hai mục). Nói đúng chiều đang xảy ra. */}
              {combined.combined.qualifiedJobs > sumOfParts && (
                <p className='text-sm text-neutral-500'>{t('combined.more', { sum: sumOfParts })}</p>
              )}
              {combined.combined.qualifiedJobs < sumOfParts && (
                <p className='text-sm text-neutral-500'>{t('combined.fewer', { sum: sumOfParts })}</p>
              )}
            </>
          )}
        </section>

        <p className='text-sm text-neutral-500'>{t('disclaimer')}</p>
      </div>
    </Page>
  );
}

export default WhatIfLayout;
