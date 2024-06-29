import React, { useCallback, useContext, useEffect, useState } from 'react';
import {
  useGetNotificationsQuery,
  useReadNotificationMutation,
} from '../../services/redux/query/usersQuery';
import { formatDistance } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { DropdownContext } from '../../context/NotificationProvider';
import useObserver from '../../hooks/useObserver';

function NotificationDropdown({ setNotReadNotifications }) {
  const { state, closeAllDropdown } = useContext(DropdownContext);
  const navigate = useNavigate();
  const [hasMore, setHasMore] = useState(true);
  const [curPage, setCurPage] = useState(1);
  const [notifications, setNotifications] = useState([]);
  const [notificationHover, setNotificationHover] = useState(null);
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
  useEffect(() => {
    if (state.visibleNotificationDropdown) {
      if (isSuccessNotifications && notificationsData) {
        setNotifications((prevNotifications) => {
          if (curPage === 1) {
            return [...notificationsData?.notifications];
          } else {
            return [
              ...new Set([
                ...prevNotifications,
                ...notificationsData?.notifications,
              ]),
            ];
          }
        });
        setNotReadNotifications(notificationsData?.notRead);
        if (notificationsData?.totalPage === curPage) {
          setHasMore(false);
        }
      }
    }
  }, [
    isSuccessNotifications,
    notificationsData,
    curPage,
    state.visibleNotificationDropdown,
  ]);
  const handleRedirect = useCallback(
    (notification) => {
      notification?.url !== null && navigate(`/${notification?.url}`);
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
    const refetch = setInterval(() => {
      setCurPage(1);
      setNotifications([]);
      setHasMore(true);
      refetchNotifications();
    }, [60000]);
    return () => clearInterval(refetch);
  }, []);
  return (
    <div
      className={`absolute w-[380px] right-0 my-1 bg-neutral-100 dark:bg-neutral-800 rounded-lg overflow-hidden shadow-lg ${
        state.visibleNotificationDropdown ? 'h-[90vh]' : 'h-0'
      } transition-all duration-200`}
    >
      <div className='p-4'>
        <h2 className='text-lg font-bold'>Notifications</h2>
      </div>
      <div className='p-4 max-h-[80vh] overflow-y-auto'>
        {notifications?.length === 0 && (
          <div>
            <p>No Notification Yet!</p>
          </div>
        )}
        <div className='flex flex-col gap-4'>
          {notifications?.map((n) => (
            <article
              key={n._id}
              className={`px-2 py-4 flex gap-2 rounded-lg cursor-pointer ${
                notificationHover === n._id
                  ? 'bg-neutral-200 dark:bg-neutral-600'
                  : ''
              }`}
              onMouseEnter={() => setNotificationHover(n._id)}
              onMouseLeave={() => setNotificationHover(null)}
              onClick={() => handleRedirect(n)}
            >
              <div className='w-1/6 overflow-hidden'>
                <img
                  className='size-[42px] rounded-full object-cover'
                  src={`${import.meta.env?.VITE_BACKEND_URL}/${
                    n.seeder.avatar.url
                  }`}
                  alt={n.seeder.username}
                />
              </div>
              <div className='w-5/6 text-base flex items-center gap-2'>
                <div className='w-5/6 flex flex-col gap-2'>
                  <p>{n.notification}</p>
                  <p className={`text-sm ${n.isRead ? '' : 'text-blue-500'}`}>
                    {formatDistance(
                      new Date(n?.created_at),
                      new Date(Date.now()),
                      {
                        addSuffix: true,
                      }
                    )}
                  </p>
                </div>
                {!n.isRead && (
                  <div className='w-1/12 flex justify-end'>
                    <span className='relative after:absolute after:w-2 after:h-2 after:bg-blue-500 after:rounded-full'></span>
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
        {hasMore && (
          <div className='text-center my-4' ref={itemRef}>
            Loading more...
          </div>
        )}
      </div>
    </div>
  );
}

export default NotificationDropdown;
