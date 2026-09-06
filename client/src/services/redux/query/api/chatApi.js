import { api } from './baseApi';

// Tin nhắn.
export const chatApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getChat: builder.query({
      query: ({ senderId, receiverId, page }) =>
        `messages/${senderId}/${receiverId}?page=${page}`,
    }),
    getNewestMessage: builder.query({
      query: () => `newest_messages`,
    }),
    readMessage: builder.mutation({
      query: (id) => ({
        url: `newest_messages/${id}`,
        method: 'PUT',
      }),
    }),
  }),
});

export const {
  useGetChatQuery,
  useLazyGetChatQuery,
  useGetNewestMessageQuery,
  useReadMessageMutation,
} = chatApi;
