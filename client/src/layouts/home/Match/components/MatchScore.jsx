import { useTranslation } from 'react-i18next';
import ScoreDial from '../../../../components/ui/ScoreDial';

/**
 * Điểm khớp hồ sơ, kèm hai chỉ số thành phần.
 *
 * Bản cũ là một con số trong viên thuốc màu xanh/vàng/xám. Đồng hồ cung tròn
 * nói được cùng lúc hai thứ mà viên thuốc không nói được: điểm này cao thấp
 * SO VỚI thang 100, và nó thuộc vùng nào — đọc được trước cả khi kịp đọc số.
 */
function MatchScore({ match, size = 'md' }) {
  const { t } = useTranslation('match');

  return (
    <div className='flex shrink-0 items-center gap-3'>
      <ScoreDial value={match.score} size={size} label={t('score.label')} />
      <dl className='text-2xs leading-tight text-fg-subtle'>
        <div className='flex gap-1'>
          <dt className='sr-only'>{t('score.semanticLabel')}</dt>
          <dd className='tnum'>
            {t('score.semantic', { percent: Math.round(match.semantic * 100) })}
          </dd>
        </div>
        <div className='mt-0.5 flex gap-1'>
          <dt>{t('score.requirement')}</dt>
          <dd className='tnum font-semibold text-fg-muted'>
            {match.requirementRatio === null
              ? t('score.noRequirement')
              : `${Math.round(match.requirementRatio * 100)}%`}
          </dd>
        </div>
      </dl>
    </div>
  );
}

export default MatchScore;
