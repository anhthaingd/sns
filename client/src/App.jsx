import { Suspense, lazy, useContext, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaXmark, FaCircleInfo, FaTriangleExclamation, FaWrench } from 'react-icons/fa6';
import Loading from './components/ui/Loading';
import Header from './components/common/Header';
import { DropdownProvider } from './context/NotificationProvider';
import { FetchDataContext } from './context/FetchDataProvider';
import { ModalContext } from './context/ModalProvider';
import { SocketContext } from './context/SocketProvider';
const ChatModal = lazy(() => import('./components/modal/ChatModal'));
const ConfirmModal = lazy(() => import('./components/modal/ConfirmModal'));
const VideoModal = lazy(() => import('./components/modal/VideoModal'));
const ToastModal = lazy(() => import('./components/modal/ToastModal'));

const ALERT_STYLES = {
  info: 'bg-accent-soft text-accent-text',
  warning: 'bg-yamabuki-100 text-yamabuki-800 dark:bg-yamabuki-800 dark:text-yamabuki-100',
  maintenance: 'bg-shu-100 text-shu-800 dark:bg-shu-800 dark:text-shu-100',
};
const ALERT_ICONS = {
  info: FaCircleInfo,
  warning: FaTriangleExclamation,
  maintenance: FaWrench,
};

const AUTH_ROUTES = ['/login', '/register'];

function App() {
  const { t } = useTranslation('common');
  const { user } = useContext(FetchDataContext);
  const { call, setMe, systemAlert, dismissSystemAlert } = useContext(SocketContext);
  const { state, setVisibleModal } = useContext(ModalContext);
  const location = useLocation();

  // `|| null` chứ không phải `if (user)`: đăng xuất xong mà `me` vẫn giữ người
  // cũ thì socket cứ nối tiếp bằng token đã bị thu hồi, và lần đăng nhập sau
  // bằng tài khoản khác sẽ dùng lại đúng kết nối mang danh tính cũ đó.
  useEffect(() => {
    setMe(user || null);
  }, [user, setMe]);

  useEffect(() => {
    if (call && call?.isReceivingCall) {
      setVisibleModal({
        visibleVideoModal: { seeder: user, receiver: call.from },
      });
    }
  }, [call, setVisibleModal, user]);

  const showShell = !AUTH_ROUTES.includes(location.pathname) && user;

  const AlertIcon = systemAlert ? (ALERT_ICONS[systemAlert.type] || FaCircleInfo) : null;

  return (
    <div className='min-h-screen bg-bg text-fg'>
      {/* Phase 5: Banner thông báo hệ thống */}
      {systemAlert && (
        <div
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium ${ALERT_STYLES[systemAlert.type] || ALERT_STYLES.info}`}
          role='alert'
        >
          {AlertIcon && <AlertIcon className='size-4 shrink-0' aria-hidden='true' />}
          <span className='flex-1'>{systemAlert.message}</span>
          <button
            type='button'
            className='shrink-0 rounded p-0.5 opacity-70 transition-opacity hover:opacity-100'
            onClick={dismissSystemAlert}
            aria-label={t('status.dismiss', 'Đóng')}
          >
            <FaXmark className='size-3.5' />
          </button>
        </div>
      )}
      {showShell && (
        <DropdownProvider>
          <Header />
        </DropdownProvider>
      )}
      <Suspense fallback={null}>
        <ToastModal />
        {user && <ChatModal />}
        {state.visibleVideoModal && <VideoModal />}
        <ConfirmModal />
      </Suspense>
      <Suspense fallback={<Loading />}>
        <Outlet />
      </Suspense>
    </div>
  );
}

export default App;
