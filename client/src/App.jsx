import { Suspense, lazy, useContext, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
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

const AUTH_ROUTES = ['/login', '/register'];

function App() {
  const { user } = useContext(FetchDataContext);
  const { call, setMe } = useContext(SocketContext);
  const { state, setVisibleModal } = useContext(ModalContext);
  const location = useLocation();

  useEffect(() => {
    if (user) setMe(user);
  }, [user, setMe]);

  useEffect(() => {
    if (call && call?.isReceivingCall) {
      setVisibleModal({
        visibleVideoModal: { seeder: user, receiver: call.from },
      });
    }
  }, [call, setVisibleModal, user]);

  const showShell = !AUTH_ROUTES.includes(location.pathname) && user;

  return (
    // Thanh trên cùng nằm NGOÀI <Suspense> của nội dung: khi chuyển sang một
    // route tải chậm, khung ứng dụng vẫn đứng yên thay vì cả trang trắng xoá.
    <div className='min-h-screen bg-bg text-fg'>
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
