import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCloudArrowUp, FaXmark } from 'react-icons/fa6';
import cn from '../../services/utils/cn';
import mediaUrl from '../../services/utils/media';
import IconButton from './IconButton';

const ACCEPT = 'image/jpeg,image/png,image/webp';

/**
 * Ô chọn ảnh có xem trước.
 *
 * Gom lại từ năm chỗ chép tay gần giống nhau (sửa bài, sửa trang cá nhân, tạo
 * và sửa channel, logo website). Ngoài việc thống nhất giao diện, ở đây còn
 * làm thêm hai thứ mà không chỗ nào trong bản cũ có:
 *   - Thả file thẳng vào khung (kéo–thả), không bắt buộc phải mở hộp chọn file.
 *   - Gỡ ảnh vừa chọn để quay lại ảnh cũ.
 *
 * @param value    File vừa chọn (chưa gửi lên)
 * @param existing ảnh đang lưu trên máy chủ: { url, name }
 */
function ImageUpload({
  value,
  existing,
  onChange,
  onRemove,
  className,
  aspect = 'aspect-video',
}) {
  const { t } = useTranslation('common');
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const preview = value ? URL.createObjectURL(value) : mediaUrl(existing);

  const pick = (file) => {
    if (file && file.type.startsWith('image/')) onChange?.(file);
  };

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <div
        role='button'
        tabIndex={0}
        className={cn(
          'flex cursor-pointer flex-col items-center justify-center gap-1.5 rounded-lg border-2 border-dashed px-4 py-6 text-center transition-colors',
          dragging
            ? 'border-accent bg-accent-soft'
            : 'border-line-strong bg-surface-2 hover:border-accent hover:bg-accent-soft/50'
        )}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          pick(e.dataTransfer.files?.[0]);
        }}
      >
        <FaCloudArrowUp className='size-5 text-accent-text' aria-hidden='true' />
        <p className='text-sm font-semibold text-fg'>{t('upload.dropHere')}</p>
        <p className='text-2xs text-fg-subtle'>{t('upload.imageHint')}</p>
      </div>

      <input
        ref={inputRef}
        className='hidden'
        type='file'
        accept={ACCEPT}
        onChange={(e) => {
          pick(e.target.files?.[0]);
          // Chọn lại đúng file vừa gỡ cũng phải kích hoạt onChange.
          e.target.value = '';
        }}
      />

      {preview && (
        <div
          className={cn(
            'relative overflow-hidden rounded-lg bg-surface-2 ring-1 ring-inset ring-line',
            aspect
          )}
        >
          <img className='size-full object-cover' src={preview} alt='' />
          {value && onRemove && (
            <IconButton
              size='sm'
              label={t('actions.delete')}
              className='absolute right-2 top-2 bg-ai-950/60 text-white hover:bg-ai-950/80 hover:text-white'
              onClick={onRemove}
            >
              <FaXmark className='size-3.5' />
            </IconButton>
          )}
        </div>
      )}
    </div>
  );
}

export default ImageUpload;
