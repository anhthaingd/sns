import { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  FaMagnifyingGlass,
  FaBell,
  FaSun,
  FaMoon,
  FaRightFromBracket,
  FaRegComments,
  FaUser,
  FaGear,
} from 'react-icons/fa6';
import { setLocalStorage } from '../../services/utils/token';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { DropdownContext } from '../../context/NotificationProvider';
import NotificationDropdown from '../dropdown/NotificationDropdown';
import SearchUsersDropdown from '../dropdown/SearchUsersDropdown';
import MessagesDropdown from '../dropdown/MessagesDropdown';
import { useLogoutUserMutation } from '../../services/redux/query/api/usersApi';
import { getWebInfo, removeUser } from '../../services/redux/slice/userSlice';
import { scrollElement } from '../../services/utils/scrollElement';
import LanguageSwitcher from './LanguageSwitcher';
import Avatar from '../ui/Avatar';
import IconButton from '../ui/IconButton';
import mediaUrl from '../../services/utils/media';
import cn from '../../services/utils/cn';

/** Huy hiệu số đếm trên nút chuông / tin nhắn. */
function CountBadge({ value }) {
  if (!value) return null;
  return (
    <span className='tnum pointer-events-none absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-pill bg-danger px-1 text-[0.625rem] font-bold text-white ring-2 ring-surface'>
      {value > 99 ? '99+' : value}
    </span>
  );
}

function Header() {
  const { t } = useTranslation('nav');
  const webInfo = useSelector(getWebInfo);
  const { user, newestMessages } = useContext(FetchDataContext);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { setVisibleDropdown } = useContext(DropdownContext);

  const [isFocus, setIsFocus] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [notReadNotifications, setNotReadNotifications] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Trạng thái ban đầu đọc từ thẻ <html>, nơi đoạn script trong index.html đã
  // đặt lớp `.dark` trước khi React chạy. Đọc lại localStorage ở đây sẽ lệch
  // với những gì đang hiển thị khi người dùng chưa từng chọn thủ công.
  const [curTheme, setTheme] = useState(() =>
    typeof document !== 'undefined' &&
    document.documentElement.classList.contains('dark')
      ? 'dark'
      : 'light'
  );
  const [logoutUser, { isSuccess: isSuccessLogout }] = useLogoutUserMutation();

  const toggleTheme = useCallback(
    () => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark')),
    []
  );

  useEffect(() => {
    document.documentElement.classList.toggle('dark', curTheme === 'dark');
    setLocalStorage('social_app_theme', curTheme);
  }, [curTheme]);

  useEffect(() => {
    if (!webInfo?.website_name) return;
    document.title = webInfo.website_name;
    const favicon = document.querySelector("link[rel~='icon']");
    const logo = mediaUrl(webInfo?.logo);
    if (favicon && logo) favicon.href = logo;
  }, [webInfo]);

  useEffect(() => {
    if (isSuccessLogout) dispatch(removeUser());
  }, [isSuccessLogout, dispatch]);

  // Menu tài khoản trước đây mở bằng `onMouseEnter`, tức là trên điện thoại
  // không có cách nào đăng xuất. Giờ mở bằng cú bấm và đóng khi bấm ra ngoài.
  useEffect(() => {
    if (!menuOpen) return undefined;
    const onPointerDown = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    const onKeyDown = (e) => e.key === 'Escape' && setMenuOpen(false);
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [menuOpen]);

  const handleRedirectToSearch = () => {
    navigate(`/search?s=${encodeURIComponent(searchValue)}&page=1`);
    setIsFocus(false);
  };

  const logo = mediaUrl(webInfo?.logo);
  const menuItemClass =
    'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg';

  return (
    <header className='sticky top-0 z-50 h-header border-b border-line bg-surface/85 backdrop-blur-md'>
      <a
        href='#fu-main'
        className='sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:z-10 focus:rounded-lg focus:bg-brand focus:px-3 focus:py-2 focus:text-sm focus:font-semibold focus:text-brand-on'
      >
        {t('skipToContent')}
      </a>

      <div className='mx-auto flex h-full max-w-shell items-center gap-2 px-3 sm:gap-4 sm:px-4'>
        {/* Nhãn hiệu */}
        <button
          type='button'
          className='group flex shrink-0 items-center gap-2'
          onClick={() => {
            scrollElement();
            navigate('/');
          }}
        >
          {logo ? (
            <img
              className='size-8 rounded-lg object-cover transition-transform group-hover:animate-sway'
              src={logo}
              alt=''
            />
          ) : (
            <img
              className='size-8 transition-transform group-hover:animate-sway'
              src='/fuurin.svg'
              alt=''
            />
          )}
          <span className='hidden font-display text-lg font-black tracking-tight text-brand-text sm:block'>
            {webInfo?.website_name || 'Fuurin'}
          </span>
        </button>

        {/* Ô tìm kiếm — trên điện thoại thu lại thành một nút */}
        <div className='relative ml-auto hidden w-full max-w-sm sm:block'>
          <FaMagnifyingGlass
            className='pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-fg-subtle'
            aria-hidden='true'
          />
          <input
            className='h-9 w-full rounded-pill bg-surface-2 pl-9 pr-3 text-sm text-fg ring-1 ring-inset ring-transparent transition-shadow placeholder:text-fg-subtle hover:bg-surface-3 focus:bg-surface focus:ring-accent'
            type='search'
            placeholder={t('searchPlaceholder')}
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onFocus={() => setIsFocus(true)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) handleRedirectToSearch();
            }}
          />
          {isFocus && (
            <SearchUsersDropdown
              searchValue={searchValue}
              setIsFocus={() => setIsFocus(false)}
            />
          )}
        </div>

        <div className='ml-auto flex items-center gap-1 sm:ml-0 sm:gap-1.5'>
          <IconButton
            className='sm:hidden'
            size='sm'
            label={t('search')}
            onClick={() => navigate('/search')}
          >
            <FaMagnifyingGlass className='size-4' />
          </IconButton>

          <div className='hidden md:block'>
            <LanguageSwitcher />
          </div>

          <IconButton size='sm' label={t('theme')} onClick={toggleTheme}>
            {curTheme === 'dark' ? (
              <FaSun className='size-4' />
            ) : (
              <FaMoon className='size-4' />
            )}
          </IconButton>

          <div className='relative'>
            <IconButton
              size='sm'
              label={t('messages')}
              onClick={() => setVisibleDropdown('visibleMessagesDropdown')}
            >
              <FaRegComments className='size-4' />
            </IconButton>
            <CountBadge value={newestMessages?.unread} />
            <MessagesDropdown />
          </div>

          <div className='relative'>
            <IconButton
              size='sm'
              label={t('notifications')}
              onClick={() => setVisibleDropdown('visibleNotificationDropdown')}
            >
              <FaBell className='size-4' />
            </IconButton>
            <CountBadge value={notReadNotifications} />
            <NotificationDropdown setNotReadNotifications={setNotReadNotifications} />
          </div>

          <div className='relative ml-0.5' ref={menuRef}>
            <button
              type='button'
              className={cn(
                'flex rounded-full ring-2 transition-all',
                menuOpen ? 'ring-accent' : 'ring-transparent hover:ring-line-strong'
              )}
              aria-haspopup='menu'
              aria-expanded={menuOpen}
              aria-label={user?.username}
              onClick={() => setMenuOpen((v) => !v)}
            >
              <Avatar src={user?.avatar} name={user?.username} size='sm' />
            </button>

            {menuOpen && (
              <div
                role='menu'
                className='absolute right-0 top-full z-10 mt-2 w-56 animate-pop overflow-hidden rounded-card bg-surface p-1.5 shadow-pop ring-1 ring-inset ring-line'
              >
                <div className='border-b border-line px-3 pb-2 pt-1.5'>
                  <p className='truncate text-sm font-bold text-fg'>
                    {user?.username}
                  </p>
                  <p className='truncate text-xs text-fg-subtle'>{user?.email}</p>
                </div>
                <div className='pt-1.5'>
                  <button
                    type='button'
                    role='menuitem'
                    className={menuItemClass}
                    onClick={() => {
                      setMenuOpen(false);
                      navigate(`/profile/${user?._id}`);
                    }}
                  >
                    <FaUser className='size-3.5' aria-hidden='true' />
                    {t('profile')}
                  </button>
                  <button
                    type='button'
                    role='menuitem'
                    className={menuItemClass}
                    onClick={() => {
                      setMenuOpen(false);
                      navigate(
                        user?.role?.value === 1 ? '/admin/settings' : '/users/settings'
                      );
                    }}
                  >
                    <FaGear className='size-3.5' aria-hidden='true' />
                    {t('settings')}
                  </button>
                  <div className='my-1.5 border-t border-line md:hidden' />
                  <div className='px-3 py-1 md:hidden'>
                    <LanguageSwitcher />
                  </div>
                  <div className='my-1.5 border-t border-line' />
                  <button
                    type='button'
                    role='menuitem'
                    className={cn(menuItemClass, 'text-danger-text hover:bg-danger-soft hover:text-danger-text')}
                    onClick={logoutUser}
                  >
                    <FaRightFromBracket className='size-3.5' aria-hidden='true' />
                    {t('logout')}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
