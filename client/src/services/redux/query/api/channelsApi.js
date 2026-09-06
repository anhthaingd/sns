import { api } from './baseApi';

// Channel và lối tắt channel ở thanh bên.
export const channelsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getAllChannels: builder.query({
      query: (search) => `channels?${search}`,
      providesTags: ['channels'],
    }),
    getChannelsByUser: builder.query({
      query: () => `channels/get_by_user`,
      providesTags: ['user_channels'],
    }),
    joinChannel: builder.mutation({
      query: (id) => ({
        url: `channels/${id}`,
        method: 'POST',
      }),
      invalidatesTags: ['channels'],
    }),
    deleteUserFromChannel: builder.mutation({
      query: ({ channelId, userId }) => ({
        url: `channels/${channelId}/delete_user`,
        method: 'DELETE',
        body: {
          userId: userId,
        },
      }),
      invalidatesTags: ['channels', 'user_channels', 'channels_details'],
    }),
    getChannelDetails: builder.query({
      query: (id) => `channels/${id}`,
      providesTags: ['channels_details'],
    }),
    createChannel: builder.mutation({
      query: (body) => ({
        url: 'channels',
        method: 'POST',
        body: body,
      }),
      invalidatesTags: ['channels'],
    }),
    updateChannel: builder.mutation({
      query: ({ id, body }) => ({
        url: `channels/${id}`,
        method: 'PUT',
        body: body,
      }),
      invalidatesTags: ['channels'],
    }),
    deleteChannel: builder.mutation({
      query: (id) => ({
        url: `channels/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['channels'],
    }),
    getShortcuts: builder.query({
      query: () => 'shortcuts',
      providesTags: ['shortcuts', 'channels', 'user_channels'],
    }),
    updateShortcut: builder.mutation({
      query: (id) => ({
        url: `shortcuts/${id}`,
        method: 'PUT',
      }),
      invalidatesTags: ['shortcuts'],
    }),
  }),
});

export const {
  useGetAllChannelsQuery,
  useGetChannelsByUserQuery,
  useJoinChannelMutation,
  useDeleteUserFromChannelMutation,
  useGetChannelDetailsQuery,
  useCreateChannelMutation,
  useUpdateChannelMutation,
  useDeleteChannelMutation,
  useGetShortcutsQuery,
  useUpdateShortcutMutation,
} = channelsApi;
