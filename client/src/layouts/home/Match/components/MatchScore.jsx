import { useTranslation } from 'react-i18next';

// Thang mau theo diem de nhin la biet ngay, khong phai doc so.
const colorOf = (score) => {
  if (score >= 75) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
  if (score >= 50) return 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200';
  return 'bg-neutral-200 text-neutral-700 dark:bg-neutral-700 dark:text-neutral-200';
};

function MatchScore({ match }) {
  const { t } = useTranslation('match');

  return (
    <div className='flex items-center gap-3'>
      <span className={`px-3 py-1 rounded-full font-bold ${colorOf(match.score)}`}>
        {match.score}
      </span>
      <div className='text-xs opacity-70 leading-tight'>
        <p>{t('score.semantic', { percent: Math.round(match.semantic * 100) })}</p>
        <p>
          {t('score.requirement')}{' '}
          {match.requirementRatio === null
            ? t('score.noRequirement')
            : `${Math.round(match.requirementRatio * 100)}%`}
        </p>
      </div>
    </div>
  );
}

export default MatchScore;
