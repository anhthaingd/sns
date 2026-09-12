import { useCallback, useContext } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { FaChevronRight } from 'react-icons/fa6';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { useGetShortcutsQuery } from '../../services/redux/query/api/channelsApi';
import Avatar from '../../components/ui/Avatar';
import { RowSkeleton } from '../../components/ui/Skeleton';
import NavSections from './NavSections';

/**
 * Cột điều hướng trái (từ breakpoint lg trở lên).
 *
 * Bản cũ là mười hai khối <button> chép tay gọi `navigate()`, không có trạng
 * thái đang chọn, và biểu tượng nhồi bằng `dangerouslySetInnerHTML`. Giờ là
 * <NavLink> thật: bấm giữa chuột mở tab mới được, trình đọc màn hình biết
 * đang ở trang nào.
 */
function LeftAside() {
  const { t } = useTranslation('nav');
  const { user, updateShortcut } = useContext(FetchDataContext);
  const navigate = useNavigate();
  const { data: shortcutsData, isLoading, isSuccess } = useGetShortcutsQuery();

  const handleRedirectShortcut = useCallback(
    (s) => {
      updateShortcut(s?.channel?._id);
      navigate(`/channels/${s?.channel?._id}`);
    },
    [updateShortcut, navigate]
  );

  const shortcuts = isSuccess ? shortcutsData?.shortcuts ?? [] : [];

  return (
    <aside className='sticky top-header hidden h-[calc(100vh-theme(spacing.header))] shrink-0 overflow-y-auto overscroll-contain border-r border-line px-3 py-5 lg:block'>
      <button
        type='button'
        className='mb-4 flex w-full items-center gap-3 rounded-card bg-surface p-2.5 text-left ring-1 ring-inset ring-line transition-colors hover:bg-surface-2'
        onClick={() => navigate(`/profile/${user?._id}`)}
      >
        <Avatar src={user?.avatar} name={user?.username} size='md' />
        <span className='min-w-0 flex-1'>
          <span className='block truncate text-sm font-bold text-fg'>
            {user?.username}
          </span>
          <span className='block truncate text-xs text-fg-subtle'>
            {t('profile')}
          </span>
        </span>
        <FaChevronRight className='size-3 shrink-0 text-fg-subtle' aria-hidden='true' />
      </button>

      <NavSections user={user} />

      <div className='mt-6 border-t border-line pt-4'>
        <h2 className='mb-1.5 px-3.5 text-2xs font-bold uppercase tracking-wider text-fg-subtle'>
          {t('shortcuts')}
        </h2>
        {isLoading && (
          <div aria-hidden='true'>
            <RowSkeleton />
            <RowSkeleton />
          </div>
        )}
        {!isLoading && shortcuts.length === 0 && (
          <p className='px-3.5 py-2 text-xs text-fg-subtle'>{t('noShortcuts')}</p>
        )}
        <div className='flex flex-col gap-0.5'>
          {shortcuts.map((s) => (
            <button
              key={s._id}
              type='button'
              className='flex items-center gap-3 rounded-lg py-2 pl-3.5 pr-3 text-left text-sm font-medium text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg'
              onClick={() => handleRedirectShortcut(s)}
            >
              <Avatar
                src={s?.channel?.background}
                name={s?.channel?.name}
                size='sm'
                className='rounded-lg'
              />
              <span className='truncate'>{s?.channel?.name}</span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}

export default LeftAside;
