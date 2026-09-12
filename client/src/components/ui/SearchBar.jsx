import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaMagnifyingGlass } from 'react-icons/fa6';
import Button from './Button';
import cn from '../../services/utils/cn';

/**
 * Ô tìm kiếm + nút Tìm + nút Đặt lại, dùng ở các bảng quản trị.
 *
 * Là một <form>, không phải ba thẻ rời như bản cũ: gõ xong nhấn Enter là tìm
 * được, không bắt buộc phải rời tay khỏi bàn phím để bấm nút.
 */
function SearchBar({ placeholder, onSearch, onReset, initialValue = '', className }) {
  const { t } = useTranslation('common');
  const [value, setValue] = useState(initialValue);

  return (
    <form
      className={cn('flex gap-2', className)}
      onSubmit={(e) => {
        e.preventDefault();
        onSearch(value.trim());
      }}
    >
      <div className='relative min-w-0 flex-1 sm:max-w-xs'>
        <FaMagnifyingGlass
          className='pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-fg-subtle'
          aria-hidden='true'
        />
        <input
          className='h-10 w-full rounded-lg bg-surface pl-9 pr-3 text-sm text-fg ring-1 ring-inset ring-line transition-shadow placeholder:text-fg-subtle focus:ring-2 focus:ring-accent'
          type='search'
          placeholder={placeholder}
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      </div>
      <Button type='submit'>{t('actions.search')}</Button>
      {onReset && (
        <Button
          type='button'
          variant='ghost'
          onClick={() => {
            setValue('');
            onReset();
          }}
        >
          {t('actions.reset')}
        </Button>
      )}
    </form>
  );
}

export default SearchBar;
