import { useCallback, useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { formatDistance } from 'date-fns';
import { FaBellSlash } from 'react-icons/fa6';
import {
  useGetNotificationsQuery,
  useReadNotificationMutation,
} from '../../services/redux/query/api/notificationsApi';
import { notificationText } from '../../services/utils/notificationText';
import { currentDateLocale } from '../../i18n/dateLocale';
import { DropdownContext } from '../../context/NotificationProvider';
import useObserver from '../../hooks/useObserver';
import Popover from '../ui/Popover';
import Avatar from '../ui/Avatar';
import Spinner from '../ui/Spinner';
import cn from '../../services/utils/cn';

/** Bao lâu thì hỏi lại máy chủ xem có thông báo mới không. */
const REFRESH_MS = 60_000;

function NotificationDropdown({ setNotReadNotifications }) {
  const { t } = useTranslation(['chat', 'common', 'error']);
  const { state, closeAllDropdown } = useContext(DropdownContext);
  const navigate = useNavigate();
  const [hasMore, setHasMore] = useState(true);
  const [curPage, setCurPage] = useState(1);
  const [notifications, setNotifications] = useState([]);
  const {
    data: notificationsData,
    isSuccess: isSuccessNotifications,
    refetch: refetchNotifications,
  } = useGetNotificationsQuery(`page=${curPage}`);
  const { itemRef } = useObserver(
    hasMore,
    curPage,
    setCurPage,
    isSuccessNotifications,
    notificationsData?.notifications,
    notificationsData?.totalPage
  );
  const [readNotification, { isSuccess: isSuccessRead }] =
    useReadNotificationMutation();

  // Số chưa đọc cập nhật NGAY khi dữ liệu về, không chờ người dùng mở bảng.
  // Bản cũ bọc cả khối này trong `if (state.visibleNotificationDropdown)`, nên
  // chấm đỏ trên chuông chỉ xuất hiện sau lần mở bảng đầu tiên — tức là đúng
  // lúc nó không còn tác dụng gì nữa.
  useEffect(() => {
    if (!isSuccessNotifications || !notificationsData) return;
    setNotReadNotifications(notificationsData?.notRead);
    setNotifications((prev) =>
      curPage === 1
        ? [...(notificationsData?.notifications || [])]
        : [...new Set([...prev, ...(notificationsData?.notifications || [])])]
    );
    if (notificationsData?.totalPage === curPage) setHasMore(false);
  }, [isSuccessNotifications, notificationsData, curPage, setNotReadNotifications]);

  const handleRedirect = useCallback(
    (notification) => {
      if (notification?.url !== null) navigate(`/${notification?.url}`);
      closeAllDropdown();
      readNotification(notification._id);
    },
    [navigate, closeAllDropdown, readNotification]
  );

  useEffect(() => {
    if (isSuccessRead) {
      setCurPage(1);
      setNotifications([]);
      setHasMore(true);
    }
  }, [isSuccessRead]);

  useEffect(() => {
    const refresh = setInterval(() => {
      setCurPage(1);
      setNotifications([]);
      setHasMore(true);
      refetchNotifications();
    }, REFRESH_MS);
    return () => clearInterval(refresh);
  }, [refetchNotifications]);

  return (
    <Popover
      open={Boolean(state.visibleNotificationDropdown)}
      onClose={closeAllDropdown}
      title={t('notifications.title')}
    >
      {notifications.length === 0 ? (
        <div className='flex flex-col items-center gap-2 px-4 py-10 text-center'>
          <FaBellSlash className='size-6 text-fg-subtle' aria-hidden='true' />
          <p className='text-sm text-fg-muted'>{t('notifications.empty')}</p>
        </div>
      ) : (
        <ul className='flex flex-col gap-0.5'>
          {notifications.map((n) => (
            <li key={n._id}>
              <button
                type='button'
                className={cn(
                  'flex w-full items-start gap-3 rounded-lg p-2.5 text-left transition-colors hover:bg-surface-2',
                  !n.isRead && 'bg-accent-soft/60'
                )}
                onClick={() => handleRedirect(n)}
              >
                <Avatar
                  src={n?.seeder?.avatar}
                  name={n?.seeder?.username}
                  size='md'
                />
                <span className='min-w-0 flex-1'>
                  <span className='block text-sm leading-snug text-fg'>
                    {notificationText(t, n)}
                  </span>
                  <span className='mt-0.5 block text-2xs text-fg-subtle'>
                    {formatDistance(new Date(n?.created_at), new Date(Date.now()), {
                      addSuffix: true,
                      locale: currentDateLocale(),
                    })}
                  </span>
                </span>
                {!n.isRead && (
                  <span
                    className='mt-2 size-2 shrink-0 rounded-full bg-accent'
                    aria-hidden='true'
                  />
                )}
              </button>
            </li>
          ))}
        </ul>
      )}

      {hasMore && notifications.length > 0 && (
        <div
          ref={itemRef}
          className='flex items-center justify-center gap-2 py-4 text-xs text-fg-subtle'
        >
          <Spinner className='size-3.5' />
          {t('common:status.loadingMore')}
        </div>
      )}
    </Popover>
  );
}

export default NotificationDropdown;
