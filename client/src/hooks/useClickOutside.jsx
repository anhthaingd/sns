import { useCallback, useContext, useRef, useEffect } from 'react';
import { ModalContext } from '../context/ModalProvider';

const useClickOutside = () => {
  const { setVisibleModal, closeAllModal } = useContext(ModalContext);
  const modalRef = useRef(null);
  const clickOutside = useCallback(
    (e) => {
      // const dialogDemission = modalRef.current?.getBoundingClientRect();
      // if (
      //   dialogDemission &&
      //   (e.clientX < dialogDemission.left ||
      //     e.clientX > dialogDemission.right ||
      //     e.clientY < dialogDemission.top ||
      //     e.clientY > dialogDemission.bottom)
      // ) {
      //   setVisibleModal(modal);
      // }
      if (modalRef.current && !modalRef.current.contains(e.target)) {
        setVisibleModal(modal);
      }
    },
    [setVisibleModal, modalRef, modal]
  );
  const handleKeyPress = useCallback(
    (e) => {
      if (e.key === 'Escape') {
        closeAllModal();
      }
    },
    [closeAllModal]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyPress);
    return () => {
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, [handleKeyPress]);
  return [modalRef, clickOutside];
};

export default useClickOutside;
