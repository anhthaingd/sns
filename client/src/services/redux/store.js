import { configureStore } from '@reduxjs/toolkit';
import { api } from './query/api/baseApi';
import userSlice from './slice/userSlice';
import { webApi } from './query/webQuery';
import { rtkQueryErrorLogger } from './middleware/errorLogger';
export const store = configureStore({
  reducer: {
    user: userSlice,
    [api.reducerPath]: api.reducer,
    [webApi.reducerPath]: webApi.reducer,
  },
  middleware: (getDefaultMiddleWare) =>
    getDefaultMiddleWare().concat(
      api.middleware,
      webApi.middleware,
      // Đứng SAU middleware của RTK Query để thấy được action rejected.
      rtkQueryErrorLogger
    ),
});
