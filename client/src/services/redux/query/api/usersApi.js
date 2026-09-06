import { api } from './baseApi';

// Tài khoản, hồ sơ cá nhân và quan hệ theo dõi.
export const usersApi = api.injectEndpoints({
  endpoints: (builder) => ({
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
    getUserDetails: builder.query({
      query: (id) => `users/${id}`,
      providesTags: ['user_details', 'users'],
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
    getSearchUsers: builder.query({
      query: (search) => ({
        url: `users?${search}`,
        method: 'GET',
      }),
    }),
    getUsersByAdmin: builder.query({
      query: (search) => `get_users_by_admin?${search}`,
    }),
  }),
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
} = usersApi;
