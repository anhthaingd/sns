import Modal from '@/modal';
import { ModalContext } from '@/context/ModalProvider';
import { useContext, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/ReactToastify.css';
const ToastModal = () => {
  const { state } = useContext(ModalContext);
  useEffect(() => {
    if (
      state.visibleToastModal &&
      state.visibleToastModal.type &&
      state.visibleToastModal.message
    ) {
      switch (state.visibleToastModal.type) {
        case 'success':
          toast.success(state.visibleToastModal.message);
          break;
        case 'error':
          toast.error(state.visibleToastModal.message);
          break;
        case 'warning':
          toast.warning(state.visibleToastModal.message);
          break;
        case 'info':
          toast.info(state.visibleToastModal.message);
          break;
        default:
          toast(state.visibleToastModal.message);
          break;
      }
    }
  }, [state.visibleToastModal]);

  return (
    <Modal>
      <ToastContainer
        position='bottom-right'
        autoClose={3000}
        newestOnTop={true}
        closeOnClick
        pauseOnFocusLoss
        stacked
      />
    </Modal>
  );
};

export default ToastModal;
