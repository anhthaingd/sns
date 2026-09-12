import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  FaLocationDot,
  FaYenSign,
  FaHouseLaptop,
  FaArrowUpRightFromSquare,
  FaArrowRight,
} from 'react-icons/fa6';
import {
  experienceLabel,
  formatSalary,
  japaneseLevelLabel,
} from '../../../../services/utils/jobFormat';
import Avatar from '../../../../components/ui/Avatar';
import Badge from '../../../../components/ui/Badge';
import Card from '../../../../components/ui/Card';
import ScoreDial from '../../../../components/ui/ScoreDial';

/** Bao nhiêu kỹ năng hiện trên thẻ trước khi gộp phần còn lại thành "+n". */
const MAX_SKILLS = 5;

/**
 * Thẻ một tin tuyển dụng.
 *
 * Trật tự thông tin bám theo thứ tự người tìm việc thật sự quét mắt: chức danh
 * → công ty → lương và địa điểm → điều kiện tiếng Nhật và kinh nghiệm → kỹ
 * năng. Lương đứng trước kỹ năng vì đó là thứ quyết định có đọc tiếp hay
 * không, mà bản cũ lại nhét nó lẫn trong một dòng meta xám nhạt.
 *
 * @param score điểm khớp 0…100, chỉ có ở các trang Match
 * @param footer nội dung phụ do trang gọi chèn thêm (ví dụ tóm tắt gap)
 */
function JobCard({ job, score, footer }) {
  const { t } = useTranslation('job');
  const companyName = job.company?.name || job.company_name;
  const skills = job.required_skills ?? [];

  return (
    <Card as='article' className='flex flex-col gap-3'>
      <div className='flex items-start gap-3'>
        <Avatar
          src={job.company?.logo_url || job.company_logo_url}
          name={companyName || '?'}
          size='lg'
          className='rounded-xl'
        />

        <div className='min-w-0 flex-1'>
          <h3 className='text-[0.9375rem] font-bold leading-snug'>
            <a
              href={job.url}
              target='_blank'
              rel='noreferrer'
              className='inline-flex items-start gap-1.5 text-fg transition-colors hover:text-accent-text'
            >
              <span className='line-clamp-2'>{job.title}</span>
              <FaArrowUpRightFromSquare
                className='mt-1 size-3 shrink-0 text-fg-subtle'
                aria-hidden='true'
              />
            </a>
          </h3>
          <p className='mt-0.5 truncate text-sm text-fg-muted'>{companyName}</p>
        </div>

        {score !== undefined && score !== null ? (
          <ScoreDial value={score} size='sm' />
        ) : (
          job.source && (
            <Badge className='shrink-0' tone='neutral'>
              {job.source}
            </Badge>
          )
        )}
      </div>

      <div className='flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm'>
        <span className='tnum flex items-center gap-1.5 font-semibold text-fg'>
          <FaYenSign className='size-3 text-fg-subtle' aria-hidden='true' />
          {formatSalary(t, job.salary_min, job.salary_max)}
        </span>
        {job.location && (
          <span className='flex min-w-0 items-center gap-1.5 text-fg-muted'>
            <FaLocationDot className='size-3 shrink-0 text-fg-subtle' aria-hidden='true' />
            <span className='truncate'>{job.location}</span>
          </span>
        )}
        {job.remote && (
          <span className='flex items-center gap-1.5 font-medium text-success-text'>
            <FaHouseLaptop className='size-3' aria-hidden='true' />
            {t('card.remote')}
          </span>
        )}
      </div>

      {(job.required_japanese ||
        job.min_years !== null ||
        skills.length > 0) && (
        <div className='flex flex-wrap gap-1.5'>
          {job.required_japanese && (
            <Badge tone='brand'>
              {t('japaneseLabel')} · {japaneseLevelLabel(t, job.required_japanese)}
            </Badge>
          )}
          {job.min_years !== null && job.min_years !== undefined && (
            <Badge tone='warning'>{experienceLabel(t, job.min_years)}</Badge>
          )}
          {skills.slice(0, MAX_SKILLS).map((s) => (
            <Badge key={s} tone='accent'>
              {s}
            </Badge>
          ))}
          {skills.length > MAX_SKILLS && (
            <Badge tone='neutral'>+{skills.length - MAX_SKILLS}</Badge>
          )}
        </div>
      )}

      {footer}

      <Link
        to={`/match/jobs/${job._id}`}
        className='group inline-flex items-center gap-1.5 self-start text-sm font-semibold text-accent-text'
      >
        {t('card.gapLink')}
        <FaArrowRight
          className='size-3 transition-transform group-hover:translate-x-0.5'
          aria-hidden='true'
        />
      </Link>
    </Card>
  );
}

export default JobCard;
