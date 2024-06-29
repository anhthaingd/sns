import { configureStore } from '@reduxjs/toolkit';
import { userApi } from './query/usersQuery';
import userSlice from './slice/userSlice';
import { webApi } from './query/webQuery';
export const store = configureStore({
  reducer: {
    user: userSlice,
    [userApi.reducerPath]: userApi.reducer,
    [webApi.reducerPath]: webApi.reducer,
  },
  middleware: (getDefaultMiddleWare) =>
    getDefaultMiddleWare().concat(userApi.middleware, webApi.middleware),
});
