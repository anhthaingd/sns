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
import { SocketContext } from '../../context/SocketProvider';
import useObserver from '../../hooks/useObserver';
import Popover from '../ui/Popover';
import Avatar from '../ui/Avatar';
import Spinner from '../ui/Spinner';
import cn from '../../services/utils/cn';

/**
 * Phase 6: KHÔNG còn polling định kỳ.
 *
 * Thông báo chính đến qua WebSocket event `notification` (tức thì). Khi socket
 * bị ngắt rồi nối lại (reconnect), SocketProvider đặt cờ `socketReconnected`
 * và component này refetch một lần để bù khoảng mất kết nối. Ngoài ra, mỗi lần
 * mở dropdown cũng refetch để đảm bảo dữ liệu mới nhất.
 */

function NotificationDropdown({ setNotReadNotifications }) {
  const { t } = useTranslation(['chat', 'common', 'error']);
  const { state, closeAllDropdown } = useContext(DropdownContext);
  const { realtimeNotifications, clearRealtimeNotifications, socketReconnected, clearSocketReconnected } =
    useContext(SocketContext);
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

  // ──────────────────────────────────────────────────────────────────────────
  // Phase 1: Nhận thông báo tức thì qua WebSocket.
  //
  // Khi SocketProvider nhận event `notification`, nó thêm vào
  // `realtimeNotifications`. Ở đây ta:
  // 1. Chèn thông báo mới lên ĐẦU danh sách (hiện ngay, không chờ refetch)
  // 2. Tăng badge chưa đọc tương ứng
  // 3. Clear danh sách real-time để tránh chèn trùng khi refetch
  // ──────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (realtimeNotifications.length === 0) return;

    setNotifications((prev) => {
      const existingIds = new Set(prev.map((n) => n._id));
      const fresh = realtimeNotifications.filter((n) => !existingIds.has(n._id));
      return [...fresh, ...prev];
    });
    setNotReadNotifications((prev) => (prev || 0) + realtimeNotifications.length);
    clearRealtimeNotifications();
  }, [realtimeNotifications, clearRealtimeNotifications, setNotReadNotifications]);

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

  // Phase 6: Refetch khi socket vừa reconnect (bù khoảng mất kết nối).
  useEffect(() => {
    if (!socketReconnected) return;
    setCurPage(1);
    setNotifications([]);
    setHasMore(true);
    refetchNotifications();
    clearSocketReconnected();
  }, [socketReconnected, refetchNotifications, clearSocketReconnected]);

  // Phase 6: Refetch mỗi lần MỞ dropdown để đảm bảo dữ liệu mới nhất.
  useEffect(() => {
    if (state.visibleNotificationDropdown) {
      setCurPage(1);
      setNotifications([]);
      setHasMore(true);
      refetchNotifications();
    }
  }, [state.visibleNotificationDropdown, refetchNotifications]);

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
