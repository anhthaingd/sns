import { useId } from 'react';
import cn from '../../services/utils/cn';

const SIZES = {
  sm: { box: 44, stroke: 4, text: 'text-xs' },
  md: { box: 64, stroke: 5, text: 'text-base' },
  lg: { box: 96, stroke: 7, text: 'text-2xl' },
};

// Ngưỡng đọc điểm. Cùng thang với GapList: xanh = nộp được, vàng = còn thiếu
// điểm cộng, đỏ = có điều kiện loại chưa đạt.
function toneOf(value) {
  if (value >= 75) return { from: '#0F8C8C', to: '#3F7D4E', text: 'text-success-text' };
  if (value >= 50) return { from: '#274A78', to: '#0F8C8C', text: 'text-accent-text' };
  return { from: '#A47522', to: '#C43C1B', text: 'text-warning-text' };
}

/**
 * Đồng hồ cung tròn cho điểm khớp hồ sơ — 0…100.
 *
 * Đây là chỗ "mạnh tay" duy nhất của giao diện: một vòng cung chuyển màu với
 * chấm tròn ở đầu mút, nhại quả lắc của chiếc chuông gió. Cung hở 270° (không
 * khép kín) để đọc được ngay đâu là đầu, đâu là cuối.
 *
 * Chỉ số dùng `tabular-nums` nên khi điểm đổi 9 → 10 con số không nhảy chỗ.
 */
function ScoreDial({ value = 0, size = 'md', label, className }) {
  const gradientId = useId();
  const { box, stroke, text } = SIZES[size] ?? SIZES.md;
  const score = Math.max(0, Math.min(100, Math.round(Number(value) || 0)));
  const tone = toneOf(score);

  const r = (box - stroke) / 2 - 1;
  const c = box / 2;
  const sweep = 0.75; // 270° — chừa một khoảng hở ở đáy
  const circumference = 2 * Math.PI * r;
  const track = circumference * sweep;
  const filled = track * (score / 100);

  return (
    <div
      className={cn('relative inline-flex shrink-0 items-center justify-center', className)}
      style={{ width: box, height: box }}
      role='img'
      aria-label={label ? `${label}: ${score}/100` : `${score}/100`}
    >
      <svg
        width={box}
        height={box}
        viewBox={`0 0 ${box} ${box}`}
        // Xoay để khoảng hở nằm dưới đáy và cung chạy từ trái sang.
        style={{ transform: 'rotate(135deg)' }}
        aria-hidden='true'
      >
        <defs>
          <linearGradient id={gradientId} x1='0' y1='0' x2='1' y2='1'>
            <stop offset='0%' stopColor={tone.from} />
            <stop offset='100%' stopColor={tone.to} />
          </linearGradient>
        </defs>
        <circle
          cx={c}
          cy={c}
          r={r}
          fill='none'
          stroke='currentColor'
          className='text-surface-3'
          strokeWidth={stroke}
          strokeLinecap='round'
          strokeDasharray={`${track} ${circumference}`}
        />
        <circle
          cx={c}
          cy={c}
          r={r}
          fill='none'
          stroke={`url(#${gradientId})`}
          strokeWidth={stroke}
          strokeLinecap='round'
          strokeDasharray={`${filled} ${circumference}`}
          style={{ transition: 'stroke-dasharray 0.6s cubic-bezier(0.22, 1, 0.36, 1)' }}
        />
      </svg>
      <span
        className={cn(
          'tnum absolute inset-0 flex items-center justify-center font-display font-bold',
          text,
          tone.text
        )}
        aria-hidden='true'
      >
        {score}
      </span>
    </div>
  );
}

export default ScoreDial;
