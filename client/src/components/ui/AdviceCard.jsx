import { useTranslation } from 'react-i18next';
import { FaWandMagicSparkles, FaRegClock } from 'react-icons/fa6';
import Card from './Card';
import Skeleton from './Skeleton';

/**
 * Lời khuyên do mô hình ngôn ngữ viết — dùng chung cho cả sáu màn hình.
 *
 * Ba nguyên tắc hiển thị, đều có lý do (xem docs/12-loi-khuyen-bang-llm.md):
 *
 * 1. **Không có thì ẩn hẳn.** Chưa cấu hình API key, hết hạn mức, nhà cung cấp
 *    hỏng — mọi trường hợp đều trả `advice: null`. Người dùng không cần biết
 *    một tính năng họ chưa từng thấy đang vắng mặt, nên ở đây KHÔNG có thông
 *    báo lỗi nào.
 * 2. **Nói rõ là do AI viết.** Phần `gaps` ngay trên là kết quả tính bằng luật,
 *    kiểm chứng được; phần này thì không. Trộn hai thứ vào một khối chữ giống
 *    nhau là để người đọc tin nhầm.
 * 3. **Luôn đứng DƯỚI phần tính bằng luật.** Thứ tự trên màn hình nói lên thứ
 *    tự đáng tin.
 */
function AdviceCard({ data, isLoading, isFetching }) {
  const { t } = useTranslation('match');

  if (isLoading || isFetching) {
    return (
      <Card className='mt-6' data-testid='advice-skeleton'>
        <div className='flex items-center gap-2 text-sm font-semibold text-fg-subtle'>
          <FaWandMagicSparkles className='size-4 animate-pulse' aria-hidden='true' />
          {t('advice.loading')}
        </div>
        <div className='mt-3 flex flex-col gap-2'>
          <Skeleton className='h-3 w-full' />
          <Skeleton className='h-3 w-11/12' />
          <Skeleton className='h-3 w-2/3' />
        </div>
      </Card>
    );
  }

  const advice = data?.advice;
  if (!advice) return null;

  return (
    <Card className='mt-6 border-l-[3px] border-brand' data-testid='advice-card'>
      <h2 className='flex items-center gap-2 text-base font-bold text-fg'>
        <FaWandMagicSparkles className='size-4 text-brand' aria-hidden='true' />
        {t('advice.title')}
      </h2>

      <p className='mt-2 text-sm leading-relaxed text-fg-muted'>{advice.summary}</p>

      {advice.roadmap?.length > 0 && (
        <ol className='mt-4 flex flex-col gap-3'>
          {advice.roadmap.map((step, index) => (
            <li
              key={`${step.title}-${index}`}
              className='flex gap-3 rounded-lg bg-surface-2 p-3'
            >
              <span className='tnum flex size-6 shrink-0 items-center justify-center rounded-full bg-brand text-xs font-bold text-white'>
                {index + 1}
              </span>
              <div className='min-w-0'>
                <p className='flex flex-wrap items-center gap-x-2 gap-y-1 text-sm font-semibold text-fg'>
                  {step.title}
                  <span className='tnum inline-flex items-center gap-1 rounded-full bg-surface px-2 py-0.5 text-2xs font-semibold text-fg-subtle'>
                    <FaRegClock className='size-3' aria-hidden='true' />
                    {t('advice.months', { count: step.months })}
                  </span>
                </p>
                <p className='mt-1 text-sm leading-relaxed text-fg-muted'>
                  {step.detail}
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}

      <p className='mt-4 text-2xs leading-relaxed text-fg-subtle'>
        {t('advice.disclaimer')}
      </p>
    </Card>
  );
}

export default AdviceCard;
