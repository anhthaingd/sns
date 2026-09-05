import React from 'react';
import { Link } from 'react-router-dom';
import { FaLocationDot, FaYenSign, FaHouseLaptop } from 'react-icons/fa6';

// Nhan hien thi cho trinh do ngon ngu da chuan hoa o backend.
export const LEVEL_LABELS = {
  none: 'Không yêu cầu',
  basic: 'Cơ bản (N4-N5)',
  conversational: 'Giao tiếp (N3)',
  business: 'Nghiệp vụ (N2)',
  fluent: 'Thành thạo (N1)',
  native: 'Bản ngữ',
};

// Backend luu luong theo YEN/NAM; nguoi Nhat doc theo don vi "man" (1 man = 10.000 yen).
export const formatSalary = (min, max) => {
  if (!min && !max) return 'Chưa công bố';
  const toMan = (v) => `${Math.round(v / 10000)} man`;
  if (min && max && min !== max) return `${toMan(min)} ~ ${toMan(max)} / năm`;
  return `${toMan(min || max)} / năm`;
};

function JobCard({ job, footer }) {
  return (
    <article className='p-4 rounded-lg border border-neutral-300 dark:border-neutral-600 bg-neutral-50 dark:bg-neutral-800 flex flex-col gap-2'>
      <div className='flex justify-between items-start gap-3'>
        <h3 className='font-bold text-base leading-snug'>
          <a href={job.url} target='_blank' rel='noreferrer' className='hover:text-blue-500'>
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
          <FaYenSign /> {formatSalary(job.salary_min, job.salary_max)}
        </span>
        {job.remote && (
          <span className='flex items-center gap-1 text-green-600 dark:text-green-400'>
            <FaHouseLaptop /> Remote
          </span>
        )}
      </div>

      <div className='flex flex-wrap gap-2 text-xs'>
        {job.required_japanese && (
          <span className='px-2 py-1 rounded bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-200'>
            🇯🇵 {LEVEL_LABELS[job.required_japanese] || job.required_japanese}
          </span>
        )}
        {job.min_years !== null && job.min_years !== undefined && (
          <span className='px-2 py-1 rounded bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'>
            {job.min_years === 0 ? 'Không cần kinh nghiệm' : `${job.min_years}+ năm KN`}
          </span>
        )}
        {job.required_skills?.slice(0, 6).map((s) => (
          <span key={s} className='px-2 py-1 rounded bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'>
            {s}
          </span>
        ))}
      </div>

      {footer}

      <Link
        to={`/match/jobs/${job._id}`}
        className='self-start text-sm text-blue-600 dark:text-blue-400 hover:underline'
      >
        Xem tôi còn thiếu gì cho vị trí này →
      </Link>
    </article>
  );
}

export default JobCard;
