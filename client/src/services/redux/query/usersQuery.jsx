import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { endpoint } from '../../../config/endpoint';
import { getAccessToken } from '../../utils/token';

export const userApi = createApi({
  reducerPath: 'userApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${endpoint}`,
    prepareHeaders: (headers) => {
      const token = getAccessToken();
      headers.set('Authorization', `Bearer ${token}`);
      return headers;
    },
  }),
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
  ],
  endpoints: (builder) => {
    return {
      getUser: builder.query({
        query: () => `users/getByToken`,
        providesTags: ['users'],
      }),
      loginUser: builder.mutation({
        query: (body) => ({
          url: 'users/login',
          method: 'POST',
          body: body,
        }),
      }),
      registerUser: builder.mutation({
        query: (body) => ({
          url: 'users/register',
          method: 'POST',
          body: body,
        }),
      }),
      logoutUser: builder.mutation({
        query: () => ({
          url: 'users/logout',
          method: 'POST',
        }),
      }),
      updateUser: builder.mutation({
        query: ({ id, body }) => ({
          url: `users/${id}`,
          method: 'PUT',
          body: body,
        }),
        invalidatesTags: ['users'],
      }),
      followingUser: builder.mutation({
        query: (id) => ({
          url: `users/${id}/following`,
          method: 'POST',
        }),
        invalidatesTags: ['users', 'user_details'],
      }),
      getFollowing: builder.query({
        query: (search) => `get_following?${search}`,
        providesTags: ['users'],
      }),
      getFollowers: builder.query({
        query: (search) => `get_followers?${search}`,
        providesTags: ['users'],
      }),
      deleteFollowing: builder.mutation({
        query: (id) => ({
          url: `remove_following/${id}`,
          method: 'DELETE',
        }),
        invalidatesTags: ['users', 'user_details'],
      }),
      deleteFollowers: builder.mutation({
        query: (id) => ({
          url: `remove_followers/${id}`,
          method: 'DELETE',
        }),
        invalidatesTags: ['users', 'user_details'],
      }),
      getUserDetails: builder.query({
        query: (id) => `users/${id}`,
        providesTags: ['user_details', 'users'],
      }),
      getSearchUsers: builder.query({
        query: (search) => ({
          url: `users?${search}`,
          method: 'GET',
        }),
      }),
      getUsersByAdmin: builder.query({
        query: (search) => `get_users_by_admin?${search}`,
      }),
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
      getPosts: builder.query({
        query: (search) => `posts?${search}`,
        providesTags: ['posts'],
      }),
      getPostDetails: builder.query({
        query: (id) => `posts/get_post_details_in_channel/${id}`,
        providesTags: ['posts'],
      }),
      getPostsByUser: builder.query({
        query: (search) => `posts/get_by_users?${search}`,
        providesTags: ['posts'],
      }),
      getPostsByAdmin: builder.query({
        query: (search) => `posts/get_by_admin?${search}`,
        providesTags: ['posts'],
      }),
      getPostsInChannel: builder.query({
        query: ({ channelId, search }) => `posts/${channelId}?${search}`,
        providesTags: ['posts'],
      }),
      getPostsFromAnotherUser: builder.query({
        query: ({ id, search }) => ({
          url: `posts/get_from_another_users/${id}?${search}`,
        }),
      }),
      createPost: builder.mutation({
        query: ({ channelId, body }) => ({
          url: `posts/${channelId}`,
          method: 'POST',
          body: body,
        }),
        invalidatesTags: ['posts'],
      }),
      updatePost: builder.mutation({
        query: ({ channelId, postId, body }) => ({
          url: `posts/${channelId}/${postId}`,
          method: 'PUT',
          body: body,
        }),
        invalidatesTags: ['posts'],
      }),
      deletePost: builder.mutation({
        query: ({ channelId, postId }) => ({
          url: `posts/${channelId}/${postId}`,
          method: 'DELETE',
        }),
        invalidatesTags: ['posts'],
      }),
      deletePostByAdmin: builder.mutation({
        query: ({ channelId, postId }) => ({
          url: `delete_post_by_admin/${channelId}/${postId}`,
          method: 'DELETE',
        }),
        invalidatesTags: ['posts'],
      }),
      likePost: builder.mutation({
        query: ({ channelId, postId }) => ({
          url: `posts/${channelId}/${postId}/like_post`,
          method: 'POST',
        }),
        invalidatesTags: ['posts'],
      }),
      bookMarkPost: builder.mutation({
        query: ({ channelId, postId }) => ({
          url: `posts/${channelId}/${postId}/book_mark`,
          method: 'POST',
        }),
        invalidatesTags: ['posts', 'bookmarks'],
      }),
      getBookMarks: builder.query({
        query: (search) => `posts/get_book_marked?${search}`,
        providesTags: ['bookmarks'],
      }),
      commentPost: builder.mutation({
        query: ({ channelId, postId, content }) => ({
          url: `posts/${channelId}/${postId}/comments`,
          method: 'POST',
          body: {
            content: content,
          },
        }),
        invalidatesTags: ['posts'],
      }),
      deleteCommentPost: builder.mutation({
        query: ({ channelId, postId, commentId }) => ({
          url: `posts/${channelId}/${postId}/comments`,
          method: 'DELETE',
          body: { commentId: commentId },
        }),
        invalidatesTags: ['posts'],
      }),
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
      getResume: builder.query({
        query: () => 'resume',
        providesTags: ['resume'],
      }),
      postResume: builder.mutation({
        query: (body) => ({
          url: 'resume',
          method: 'POST',
          body: body,
        }),
        invalidatesTags: ['resume'],
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
    };
  },
});
export const {
  useGetUserQuery,
  useLoginUserMutation,
  useRegisterUserMutation,
  useLogoutUserMutation,
  useUpdateUserMutation,
  useFollowingUserMutation,
  useGetUserDetailsQuery,
  useGetFollowingQuery,
  useGetFollowersQuery,
  useDeleteFollowingMutation,
  useDeleteFollowersMutation,
  useGetSearchUsersQuery,
  useGetUsersByAdminQuery,
  useGetAllChannelsQuery,
  useJoinChannelMutation,
  useDeleteUserFromChannelMutation,
  useGetChannelsByUserQuery,
  useGetPostsQuery,
  useGetPostsByAdminQuery,
  useGetPostDetailsQuery,
  useGetPostsByUserQuery,
  useGetPostsInChannelQuery,
  useGetPostsFromAnotherUserQuery,
  useCreatePostMutation,
  useUpdatePostMutation,
  useDeletePostMutation,
  useDeletePostByAdminMutation,
  useLikePostMutation,
  useBookMarkPostMutation,
  useGetBookMarksQuery,
  useCommentPostMutation,
  useDeleteCommentPostMutation,
  useGetNotificationsQuery,
  useReadNotificationMutation,
  useGetChannelDetailsQuery,
  useCreateChannelMutation,
  useUpdateChannelMutation,
  useDeleteChannelMutation,
  useGetShortcutsQuery,
  useUpdateShortcutMutation,
  useGetResumeQuery,
  usePostResumeMutation,
  useGetNewestMessageQuery,
  useReadMessageMutation,
} = userApi;
