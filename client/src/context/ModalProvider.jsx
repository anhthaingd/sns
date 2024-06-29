import { createContext, useCallback, useReducer } from 'react';

const SET_VISIBLE_MODAL = 'SET_VISIBLE_MODAL';
const CLOSE_ALL_MODAL = 'CLOSE_ALL_MODAL';
const reducer = (state, action) => {
  const currentModal = action.payload?.modal;
  const resetState = {};
  switch (action.type) {
    case SET_VISIBLE_MODAL:
      if (typeof action.payload?.modal === 'object') return currentModal;
      if (currentModal === null) return { ...resetState };
      return {
        ...resetState,
        [currentModal]: !state[currentModal],
      };
    case CLOSE_ALL_MODAL:
      return { ...resetState };

    default:
      return state;
  }
};
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
