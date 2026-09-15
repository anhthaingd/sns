import { createContext, useCallback, useReducer } from 'react';

const SET_VISIBLE_MODAL = 'SET_VISIBLE_MODAL';
const CLOSE_ALL_MODAL = 'CLOSE_ALL_MODAL';
const initialState = {
  visibleToastModal: null,
  visibleAddChannelModal: false,
  visibleListMembersModal: null,
  visibleUpdateChannelModal: null,
  visibleUpdateProfileModal: false,
  visibleUpdatePostModal: null,
  visibleConfirmModal: null,
  visibleResumeModal: null,
  visibleVideoModal: null,
};
/**
 * Toast là lớp thông báo NỔI, không phải một modal: hiện toast không được đóng
 * modal đang mở, và đóng modal không được xoá toast vừa hiện.
 *
 * Vì sao phải nói rõ: bản cũ trả về thẳng object được truyền vào
 * (`return currentModal`), tức là THAY nguyên trạng thái chứ không trộn. Nên
 * luồng "lưu thành công" — `useMutationToast` hiện toast rồi gọi `close()` —
 * chạy thành hai bước phá nhau:
 *
 *   1. hiện toast  -> state chỉ còn `{ visibleToastModal }`, mọi cờ khác biến mất
 *   2. `close()`   -> `!state['visibleUpdateProfileModal']` đọc phải `undefined`
 *                     nên đảo thành `true`, đồng thời xoá luôn toast
 *
 * Kết quả: lưu xong thì modal KHÔNG đóng và toast thành công KHÔNG hiện — dù
 * request đã 200. Lỗi này dính mọi modal có nút lưu (hồ sơ, channel, bài viết).
 */
const reducer = (state, action) => {
  const currentModal = action.payload?.modal;
  // Đóng hết modal nhưng giữ nguyên toast đang hiện.
  const closedState = { ...initialState, visibleToastModal: state.visibleToastModal };
  switch (action.type) {
    case SET_VISIBLE_MODAL: {
      if (currentModal === null) return closedState;
      if (typeof currentModal === 'object') {
        const onlyToast = Object.keys(currentModal).every(
          (key) => key === 'visibleToastModal'
        );
        // Hiện toast: giữ nguyên mọi thứ đang mở.
        if (onlyToast) return { ...state, ...currentModal };
        // Mở một modal: đóng các modal khác, giữ toast.
        return { ...closedState, ...currentModal };
      }
      return {
        ...closedState,
        [currentModal]: !state[currentModal],
      };
    }
    case CLOSE_ALL_MODAL:
      return closedState;

    default:
      return state;
  }
};
export const ModalContext = createContext();

export const ModalProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);
  const setVisibleModal = useCallback((modal) => {
    dispatch({ type: SET_VISIBLE_MODAL, payload: { modal } });
  }, []);
  const closeAllModal = useCallback(() => {
    dispatch({ type: CLOSE_ALL_MODAL });
  }, []);
  const contextValue = {
    state,
    setVisibleModal,
    closeAllModal,
  };
  return (
    <ModalContext.Provider value={contextValue}>
      {children}
    </ModalContext.Provider>
  );
};
