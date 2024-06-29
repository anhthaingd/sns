import ReactDOM from 'react-dom';
function Modal({ children }) {
  const modalRoot = document.getElementById('modal');
  if (!modalRoot) {
    throw new Error('Modal root element not found!');
  }

  return ReactDOM.createPortal(children, modalRoot);
}

export default Modal;
