import React, { Suspense, lazy, useContext, useEffect } from 'react';
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

function App() {
  const { user } = useContext(FetchDataContext);
  const { call, setMe } = useContext(SocketContext);
  const { state, setVisibleModal } = useContext(ModalContext);
  const disallowAppExtensions = ['/login', '/register'];
  const location = useLocation();

  useEffect(() => {
    if (user) {
      setMe(user);
    }
  }, [user, setMe]);
  useEffect(() => {
    if (call && call?.isReceivingCall) {
      setVisibleModal({
        visibleVideoModal: {
          seeder: user,
          receiver: call.from,
        },
      });
    }
  }, [call, setVisibleModal, user]);

  return (
    <Suspense
      fallback={<Loading />}
      className='grid grid-cols-4 gap-8 place-items-center'
    >
      {!disallowAppExtensions.includes(location.pathname) && user && (
        <DropdownProvider>
          <Header />
        </DropdownProvider>
      )}
      <ToastModal />
      {user && <ChatModal />}
      {state.visibleVideoModal && <VideoModal />}
      <ConfirmModal />
      <Outlet />
    </Suspense>
  );
}

export default App;
