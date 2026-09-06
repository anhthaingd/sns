import { api } from './baseApi';

// Thông báo.
export const notificationsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getNotifications: builder.query({
      query: (search) => `notifications?${search}`,
      providesTags: ['notifications'],
    }),
    readNotification: builder.mutation({
      query: (id) => ({
        url: `notifications/${id}`,
        method: 'POST',
      }),
      invalidatesTags: ['notifications'],
    }),
  }),
});

export const {
  useGetNotificationsQuery,
  useReadNotificationMutation,
} = notificationsApi;
