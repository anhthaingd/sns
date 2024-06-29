import React, {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { getLocalStorage, setLocalStorage } from '../../services/utils/token';
import { useDispatch } from 'react-redux';
import {
  FaMagnifyingGlass,
  FaBell,
  FaSun,
  FaMoon,
  FaArrowRightFromBracket,
  FaFacebookMessenger,
} from 'react-icons/fa6';
import { FetchDataContext } from '../../context/FetchDataProvider';
import NotificationDropdown from '../dropdown/NotificationDropdown';
import { DropdownContext } from '../../context/NotificationProvider';
import SearchUsersDropdown from '../dropdown/SearchUsersDropdown';
import { useLogoutUserMutation } from '../../services/redux/query/usersQuery';
import { getWebInfo, removeUser } from '../../services/redux/slice/userSlice';
import { useNavigate } from 'react-router-dom';
import { scrollElement } from '../../services/utils/scrollElement';
import { useSelector } from 'react-redux';
import MessagesDropdown from '../dropdown/MessagesDropdown';
function Header() {
  const webInfo = useSelector(getWebInfo);
  const { user, newestMessages } = useContext(FetchDataContext);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const searchInputRef = useRef();
  const [isFocus, setIsFocus] = useState(false);
  const { setVisibleDropdown } = useContext(DropdownContext);
  const [searchValue, setSearchValue] = useState('');
  const [notReadNotifications, setNotReadNotifications] = useState(0);
  const [curTheme, setTheme] = useState(
    getLocalStorage('social_app_theme') || 'dark'
  );
  const [isLogout, setIsLogout] = useState(false);
  const [logoutUser, { isSuccess: isSuccessLogout }] = useLogoutUserMutation();
  const toggleTheme = useCallback(() => {
    setTheme((prevTheme) => {
      if (prevTheme === 'dark') return 'light';
      if (prevTheme === 'light') return 'dark';
      return 'dark';
    });
  }, [curTheme]);
  const redirectToHomePage = () => {
    scrollElement();
    navigate('/');
  };
  useEffect(() => {
    document.title = webInfo?.website_name || 'App';
    const favicon = document.querySelector("link[rel~='icon']");
    if (favicon) {
      favicon.href = `${import.meta.env.VITE_BACKEND_URL}/${
        webInfo?.logo?.url
      }`;
    }
  }, []);
  useEffect(() => {
    if (curTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    setLocalStorage('social_app_theme', curTheme);
  }, [curTheme]);
  useEffect(() => {
    if (isSuccessLogout) {
      dispatch(removeUser());
    }
  }, [isSuccessLogout, dispatch]);
  const handleSetNotReadNotification = (amount) => {
    setNotReadNotifications(amount);
  };
  const handleRedirectToSearch = () => {
    navigate(`/search?s=${searchValue}&page=1`);
    setIsFocus(false);
  };
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleRedirectToSearch();
    }
  };
  return (
    <header className='fixed top-0 left-0 w-full h-[56px] z-50 px-4 py-2 text-neutral-700 bg-neutral-100 dark:bg-neutral-700 dark:text-neutral-300 flex justify-between items-center gap-8 text-sm md:text-base border-b border-neutral-300 shadow-lg'>
      <div className='flex items-stretch gap-4'>
        <div className='flex items-center gap-2'>
          <div className='size-[42px] overflow-hidden'>
            <img
              className='w-full h-full cursor-pointer'
              src={`${import.meta.env.VITE_BACKEND_URL}/${webInfo?.logo?.url}`}
              alt={webInfo?.logo?.name}
              onClick={redirectToHomePage}
            />
          </div>
          <h1
            className='text-2xl font-bold'
            style={{ color: webInfo?.color_title }}
          >
            {webInfo?.website_name}
          </h1>
        </div>
        <div className='relative w-[240px] flex items-center'>
          <FaMagnifyingGlass
            className='absolute top-1/2 left-3 -translate-y-1/2  cursor-pointer'
            onClick={handleRedirectToSearch}
          />
          <input
            ref={searchInputRef}
            className='w-full py-2 px-8 rounded-3xl bg-neutral-200 dark:bg-neutral-600'
            type='text'
            placeholder='Search...'
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onClick={() => setIsFocus(true)}
            onKeyDown={handleKeyDown}
          />
          {isFocus && (
            <SearchUsersDropdown
              searchValue={searchValue}
              setIsFocus={() => setIsFocus(false)}
            />
          )}
        </div>
      </div>
      <div className='flex items-center gap-4'>
        <button
          className='size-[40px] rounded-full overflow-hidden flex justify-center items-center bg-neutral-200 dark:bg-neutral-600'
          onClick={toggleTheme}
        >
          {curTheme === 'dark' ? (
            <FaSun className='text-xl' />
          ) : (
            <FaMoon className='text-xl' />
          )}
        </button>
        <div className='relative'>
          <button
            className='size-[40px] rounded-full overflow-hidden flex justify-center items-center bg-neutral-200 dark:bg-neutral-600'
            onClick={() => setVisibleDropdown('visibleMessagesDropdown')}
          >
            <FaFacebookMessenger className='text-xl' />
          </button>
          {newestMessages?.unread > 0 && (
            <span className='absolute size-[20px] -top-[20%] -right-[10%] bg-red-500 text-neutral-100 text-sm rounded-full flex justify-center items-center'>
              {newestMessages?.unread}
            </span>
          )}
          <MessagesDropdown />
        </div>
        <div className='relative'>
          <button
            className='size-[40px] rounded-full overflow-hidden flex justify-center items-center bg-neutral-200 dark:bg-neutral-600'
            onClick={() => setVisibleDropdown('visibleNotificationDropdown')}
          >
            <FaBell className='text-xl' />
          </button>
          {notReadNotifications > 0 && (
            <span className='absolute size-[20px] -top-[20%] -right-[10%] bg-red-500 text-neutral-100 text-sm rounded-full flex justify-center items-center'>
              {notReadNotifications}
            </span>
          )}
          <NotificationDropdown
            setNotReadNotifications={handleSetNotReadNotification}
          />
        </div>
        <div
          className='relative'
          onMouseEnter={() => setIsLogout(true)}
          onMouseLeave={() => setIsLogout(false)}
        >
          <button className='size-[40px] rounded-full overflow-hidden'>
            <img
              className='w-full h-full object-cover'
              src={`${import.meta.env.VITE_BACKEND_URL}/${user?.avatar?.url}`}
              alt={user?.username}
            />
          </button>
          {isLogout && (
            <button
              className='absolute right-0 top-[100%] px-4 py-2 flex items-center gap-4 bg-neutral-200 dark:bg-neutral-800 font-bold rounded'
              onClick={logoutUser}
            >
              <FaArrowRightFromBracket />
              <span>Logout</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
