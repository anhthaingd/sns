import { createSlice } from '@reduxjs/toolkit';
import {
  deleteLocalStorage,
  getAccessToken,
  setLocalStorage,
} from '../../utils/token';

export const userSlice = createSlice({
  name: 'user',
  initialState: {
    user: null,
    token: getAccessToken() || null,
    webInfo: null,
  },
  reducers: {
    setToken: (state, action) => {
      state.token = action.payload;
      setLocalStorage('social_app_token', action.payload);
    },
    setUser: (state, action) => {
      state.user = action.payload;
    },
    setWebInfo: (state, action) => {
      state.webInfo = action.payload;
    },
    removeUser: (state, _) => {
      state.user = null;
      state.token = null;
      deleteLocalStorage('social_app_token');
    },
  },
});

export const { setToken, setUser, removeUser, setWebInfo } = userSlice.actions;
export const getToken = (state) => state.user.token;
export const getUser = (state) => state.user.user;
export const getWebInfo = (state) => state.user.webInfo;
export default userSlice.reducer;
