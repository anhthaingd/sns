import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQueryWithReauth } from '../baseQuery';

/**
 * Một API slice duy nhất, các domain tự "tiêm" endpoint của mình vào.
 *
 * Trước đây toàn bộ 54 endpoint nằm trong một file tên `usersQuery.jsx` —
 * trong đó có cả bài viết, channel, việc làm, chat, thông báo. Mở file ra
 * không biết tìm ở đâu, và mọi thay đổi dù nhỏ đều đụng vào một file 384 dòng
 * mà cả nhóm cùng sửa.
 *
 * Vẫn giữ MỘT `createApi`: tách thành nhiều API slice sẽ mất khả năng cho
 * mutation ở domain này làm mới cache của domain kia (ví dụ lưu CV phải làm
 * mới danh sách công ty phù hợp). `injectEndpoints` cho ta tách file mà vẫn
 * chung một kho cache và một hàng đợi tag.
 *
 * `reducerPath` giữ nguyên 'userApi' để không phải đụng vào store.
 */
export const api = createApi({
  reducerPath: 'userApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: [
    'users',
    'posts',
    'channels',
    'user_channels',
    'notifications',
    'search_users',
    'user_details',
    'bookmarks',
    'channels_details',
    'shortcuts',
    'resume',
    'jobs',
    'companies',
    'matches',
  ],
  endpoints: () => ({}),
});

export default api;
