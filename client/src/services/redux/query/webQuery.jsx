import { createApi } from '@reduxjs/toolkit/query/react';
import { baseQueryWithReauth } from './baseQuery';
export const webApi = createApi({
  reducerPath: 'webApi',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['website'],
  endpoints: (builder) => {
    return {
      getWeb: builder.query({
        query: () => `website`,
        providesTags: ['website'],
      }),
      updateWeb: builder.mutation({
        query: ({ id, body }) => ({
          url: `website/${id}`,
          method: 'PUT',
          body: body,
        }),
        invalidatesTags: ['website'],
      }),
    };
  },
});

export const { useGetWebQuery, useUpdateWebMutation } = webApi;
