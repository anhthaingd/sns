import { useState } from 'react';
import cn from '../../services/utils/cn';
import mediaUrl from '../../services/utils/media';

const SIZES = {
  xs: 'size-6 text-[10px]',
  sm: 'size-8 text-xs',
  md: 'size-10 text-sm',
  lg: 'size-12 text-base',
  xl: 'size-16 text-xl',
  '2xl': 'size-24 text-3xl sm:size-32 sm:text-4xl',
};

/**
 * Sáu sắc độ chàm/asagi, chọn theo tên nên cùng một người luôn ra cùng một màu
 * — ảnh thay thế vì thế nhận diện được chứ không phải một ô xám vô danh.
 */
const TINTS = [
  'bg-ai-100 text-ai-700 dark:bg-ai-900 dark:text-ai-200',
  'bg-asagi-100 text-asagi-700 dark:bg-asagi-900 dark:text-asagi-200',
  'bg-shu-100 text-shu-700 dark:bg-shu-900 dark:text-shu-200',
  'bg-matcha-100 text-matcha-700 dark:bg-matcha-700 dark:text-matcha-100',
  'bg-yamabuki-100 text-yamabuki-700 dark:bg-yamabuki-700 dark:text-yamabuki-100',
  'bg-ai-200 text-ai-800 dark:bg-ai-800 dark:text-ai-100',
];

function initials(name = '') {
  const parts = String(name).trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '?';
  // Tên tiếng Nhật/Trung thường viết liền không dấu cách: lấy ký tự đầu là đủ.
  if (parts.length === 1) return parts[0].slice(0, 1).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function tintOf(name = '') {
  let hash = 0;
  for (let i = 0; i < name.length; i += 1) hash = (hash * 31 + name.charCodeAt(i)) | 0;
  return TINTS[Math.abs(hash) % TINTS.length];
}

/**
 * Ảnh đại diện có ảnh thay thế.
 *
 * Trước đây mỗi nơi tự nối chuỗi URL, ảnh thiếu thì hiện biểu tượng vỡ. Ở đây
 * cả trường hợp thiếu URL lẫn trường hợp tải lỗi đều rơi về chữ cái đầu tên.
 */
function Avatar({
  src,
  name = '',
  size = 'md',
  ring = false,
  status,
  className,
  ...rest
}) {
  const [failed, setFailed] = useState(false);
  const url = mediaUrl(src);
  const showImage = url && !failed;

  return (
    <span
      className={cn(
        'relative inline-flex shrink-0 select-none items-center justify-center overflow-hidden rounded-full font-semibold',
        SIZES[size] ?? SIZES.md,
        !showImage && tintOf(name),
        ring && 'ring-2 ring-surface',
        className
      )}
      {...rest}
    >
      {showImage ? (
        <img
          className='size-full object-cover'
          src={url}
          alt={name}
          loading='lazy'
          decoding='async'
          onError={() => setFailed(true)}
        />
      ) : (
        <span aria-hidden='true'>{initials(name)}</span>
      )}
      {!showImage && <span className='sr-only'>{name}</span>}
      {status && (
        <span
          className={cn(
            'absolute bottom-0 right-0 block size-1/4 rounded-full ring-2 ring-surface',
            status === 'online' ? 'bg-success' : 'bg-fg-subtle'
          )}
        />
      )}
    </span>
  );
}

export default Avatar;
