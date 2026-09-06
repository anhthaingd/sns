import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaLocationDot, FaYenSign, FaHouseLaptop } from 'react-icons/fa6';
import {
  experienceLabel,
  formatSalary,
  japaneseLevelLabel,
} from '../../../../services/utils/jobFormat';

function JobCard({ job, footer }) {
  const { t } = useTranslation('job');

  return (
    <article className='p-4 rounded-lg border border-neutral-300 dark:border-neutral-600 bg-neutral-50 dark:bg-neutral-800 flex flex-col gap-2'>
      <div className='flex justify-between items-start gap-3'>
        <h3 className='font-bold text-base leading-snug'>
          <a
            href={job.url}
            target='_blank'
            rel='noreferrer'
            className='hover:text-blue-500'
          >
            {job.title}
          </a>
        </h3>
        <span className='shrink-0 text-xs px-2 py-1 rounded bg-neutral-200 dark:bg-neutral-700'>
          {job.source}
        </span>
      </div>

      <p className='text-sm opacity-80'>{job.company?.name || job.company_name}</p>

      <div className='flex flex-wrap gap-x-4 gap-y-1 text-sm opacity-80'>
        {job.location && (
          <span className='flex items-center gap-1'>
            <FaLocationDot /> {job.location}
          </span>
        )}
        <span className='flex items-center gap-1'>
          <FaYenSign /> {formatSalary(t, job.salary_min, job.salary_max)}
        </span>
        {job.remote && (
          <span className='flex items-center gap-1 text-green-600 dark:text-green-400'>
            <FaHouseLaptop /> {t('card.remote')}
          </span>
        )}
      </div>

      <div className='flex flex-wrap gap-2 text-xs'>
        {job.required_japanese && (
          <span className='px-2 py-1 rounded bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-200'>
            🇯🇵 {japaneseLevelLabel(t, job.required_japanese)}
          </span>
        )}
        {job.min_years !== null && job.min_years !== undefined && (
          <span className='px-2 py-1 rounded bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'>
            {experienceLabel(t, job.min_years)}
          </span>
        )}
        {job.required_skills?.slice(0, 6).map((s) => (
          <span
            key={s}
            className='px-2 py-1 rounded bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
          >
            {s}
          </span>
        ))}
      </div>

      {footer}

      <Link
        to={`/match/jobs/${job._id}`}
        className='self-start text-sm text-blue-600 dark:text-blue-400 hover:underline'
      >
        {t('card.gapLink')}
      </Link>
    </article>
  );
}

export default JobCard;
