import { useCallback, useContext, useRef, useEffect } from 'react';
import { ModalContext } from '../context/ModalProvider';

const useClickOutside = () => {
  const { closeAllModal } = useContext(ModalContext);
  const modalRef = useRef(null);
  const clickOutside = useCallback(
    (e) => {
      if (modalRef.current && !modalRef.current.contains(e.target)) {
        // Trước đây gọi `setVisibleModal(modal)` với `modal` KHÔNG hề được khai
        // báo ở đâu cả. Nó không nổ ReferenceError chỉ vì `index.html` có
        // `<div id="modal">`, mà trình duyệt thì tự tạo biến toàn cục theo id
        // phần tử — nên `modal` vô tình trỏ vào cái div đó và cả state modal bị
        // gán bằng một node DOM. Đổi tên div đó là 7 modal hỏng cùng lúc.
        // `closeAllModal` mới đúng ý định: bấm ra ngoài thì đóng modal, y như
        // khi bấm phím Escape ở dưới.
        closeAllModal();
      }
    },
    [modalRef, closeAllModal]
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
