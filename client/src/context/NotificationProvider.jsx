import { createContext, useCallback, useReducer } from 'react';

const SET_VISIBLE_DROPDOWN = 'SET_VISIBLE_DROPDOWN';
const CLOSE_ALL_DROPDOWN = 'CLOSE_ALL_DROPDOWN';
const reducer = (state, action) => {
  const currentModal = action.payload?.dropdown;
  const resetState = {};
  switch (action.type) {
    case SET_VISIBLE_DROPDOWN:
      if (currentModal === null) return { ...resetState };
      return {
        ...resetState,
        [currentModal]: !state[currentModal],
      };
    case CLOSE_ALL_DROPDOWN:
      return { ...resetState };

    default:
      return state;
  }
};
const initialState = {
  visibleUserDropdown: false,
  visibleNotificationDropdown: false,
  visibleSearchUsersDropdown: false,
};
export const DropdownContext = createContext();

export const DropdownProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);
  const setVisibleDropdown = useCallback((dropdown) => {
    dispatch({ type: SET_VISIBLE_DROPDOWN, payload: { dropdown } });
  }, []);
  const closeAllDropdown = useCallback(() => {
    dispatch({ type: CLOSE_ALL_DROPDOWN });
  }, []);
  const contextValue = {
    state,
    setVisibleDropdown,
    closeAllDropdown,
  };
  return (
    <DropdownContext.Provider value={contextValue}>
      {children}
    </DropdownContext.Provider>
  );
};
