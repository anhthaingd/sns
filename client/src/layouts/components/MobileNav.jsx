import { useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { FaBars, FaXmark, FaRightFromBracket } from 'react-icons/fa6';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { useLogoutUserMutation } from '../../services/redux/query/api/usersApi';
import Avatar from '../../components/ui/Avatar';
import Button from '../../components/ui/Button';
import cn from '../../services/utils/cn';
import { MOBILE_NAV } from './navItems';
import NavSections from './NavSections';

/**
 * Điều hướng cho màn hình hẹp — phần trước đây hoàn toàn không có.
 *
 * Bản cũ giấu cả hai cột bên (`hidden lg:flex`) nhưng vẫn giữ nguyên
 * `pl-[360px] pr-[330px]` ở khung nội dung, nên trên điện thoại người dùng
 * thấy một dải trống 690px và KHÔNG có cách nào đi sang trang khác ngoài
 * logo về trang chủ.
 *
 * Gồm hai phần: thanh cố định dưới đáy với bốn đích hay dùng nhất, và ngăn
 * kéo chứa toàn bộ menu.
 */
function MobileNav() {
  const { t } = useTranslation('nav');
  const { user } = useContext(FetchDataContext);
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const [logoutUser] = useLogoutUserMutation();

  // Đổi trang thì đóng ngăn kéo. Không có dòng này, bấm một mục xong ngăn kéo
  // vẫn che kín trang vừa mở.
  useEffect(() => setOpen(false), [location.pathname]);

  useEffect(() => {
    if (!open) return undefined;
    const { overflow } = document.body.style;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = overflow;
    };
  }, [open]);

  const itemClass = ({ isActive }) =>
    cn(
      'relative flex flex-1 flex-col items-center justify-center gap-1 py-2 text-[0.625rem] font-semibold transition-colors',
      isActive ? 'text-accent-text' : 'text-fg-subtle'
    );

  return (
    <>
      <nav
        className='fixed inset-x-0 bottom-0 z-40 flex items-stretch border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden'
        aria-label={t('menu')}
      >
        {MOBILE_NAV.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={itemClass}>
            {({ isActive }) => (
              <>
                <item.icon className='size-5' aria-hidden='true' />
                <span className='max-w-full truncate px-1'>{t(item.labelKey)}</span>
                {isActive && (
                  <span
                    className='absolute top-0 h-0.5 w-10 rounded-b-pill bg-accent'
                    aria-hidden='true'
                  />
                )}
              </>
            )}
          </NavLink>
        ))}
        <button
          type='button'
          className='flex flex-1 flex-col items-center justify-center gap-1 py-2 text-[0.625rem] font-semibold text-fg-subtle'
          onClick={() => setOpen(true)}
          aria-expanded={open}
        >
          <FaBars className='size-5' aria-hidden='true' />
          <span>{t('more')}</span>
        </button>
      </nav>

      {open && (
        <div
          className='fixed inset-0 z-[80] animate-fade-in bg-ai-950/60 backdrop-blur-sm lg:hidden'
          onClick={() => setOpen(false)}
        >
          <div
            className='ml-auto flex h-full w-[19rem] max-w-[85vw] animate-rise flex-col overflow-y-auto bg-bg shadow-modal'
            onClick={(e) => e.stopPropagation()}
          >
            <div className='flex items-center justify-between border-b border-line px-4 py-3'>
              <button
                type='button'
                className='flex min-w-0 items-center gap-3 text-left'
                onClick={() => navigate(`/profile/${user?._id}`)}
              >
                <Avatar src={user?.avatar} name={user?.username} size='md' />
                <span className='truncate text-sm font-bold'>{user?.username}</span>
              </button>
              <button
                type='button'
                className='rounded-full p-2 text-fg-muted hover:bg-surface-2'
                onClick={() => setOpen(false)}
                aria-label={t('closeMenu')}
              >
                <FaXmark className='size-5' />
              </button>
            </div>

            <div className='flex-1 px-3 py-4'>
              <NavSections user={user} onNavigate={() => setOpen(false)} />
            </div>

            <div className='border-t border-line p-3'>
              <Button
                variant='ghost'
                size='sm'
                block
                icon={FaRightFromBracket}
                className='justify-start text-danger-text hover:bg-danger-soft'
                onClick={logoutUser}
              >
                {t('logout')}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default MobileNav;
