import { fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { endpoint } from '../../../config/endpoint';
import { getAccessToken, setLocalStorage } from '../../utils/token';
import { removeUser, setToken } from '../slice/userSlice';

/**
 * Base query dùng chung cho mọi API slice.
 *
 * Access token giờ chỉ sống 15 phút, nên nếu không tự gia hạn thì người dùng
 * sẽ bị đá ra màn hình đăng nhập giữa chừng. Ở đây: gặp 401 thì gọi
 * `POST /api/users/refresh` một lần (refresh token nằm trong cookie httpOnly,
 * `credentials: 'include'` mới gửi kèm được) rồi thử lại request cũ.
 */
const rawBaseQuery = fetchBaseQuery({
  baseUrl: `${endpoint}`,
  // Bắt buộc để trình duyệt gửi cookie refresh_token kèm request.
  credentials: 'include',
  prepareHeaders: (headers) => {
    const token = getAccessToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  },
});

// Nhiều query có thể cùng nhận 401 một lúc (trang chủ gọi 4-5 endpoint song
// song). Dùng chung một promise để chỉ gọi refresh ĐÚNG MỘT LẦN — gọi nhiều lần
// sẽ xoay vòng refresh token liên tục và tự thu hồi lẫn nhau.
let refreshPromise = null;

const refreshOnce = async (api, extraOptions) => {
  if (!refreshPromise) {
    refreshPromise = rawBaseQuery(
      { url: 'users/refresh', method: 'POST' },
      api,
      extraOptions
    ).finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
};

export const baseQueryWithReauth = async (args, api, extraOptions) => {
  const result = await rawBaseQuery(args, api, extraOptions);

  if (result?.error?.status !== 401) {
    return result;
  }

  const url = typeof args === 'string' ? args : args?.url;
  // Không tự refresh cho chính route auth: 401 ở đó nghĩa là phiên đã hết thật.
  if (url === 'users/refresh' || url === 'users/login') {
    return result;
  }

  const refreshResult = await refreshOnce(api, extraOptions);
  if (!refreshResult?.data?.accessToken) {
    api.dispatch(removeUser());
    return result;
  }

  setLocalStorage('social_app_token', refreshResult.data.accessToken);
  api.dispatch(setToken(refreshResult.data.accessToken));
  // prepareHeaders đọc lại localStorage nên lần thử này mang token mới.
  return rawBaseQuery(args, api, extraOptions);
};
