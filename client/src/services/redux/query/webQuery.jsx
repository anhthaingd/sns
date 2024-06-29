import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { endpoint } from '../../../config/endpoint';
import { getAccessToken } from '../../utils/token';
export const webApi = createApi({
  reducerPath: 'webApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${endpoint}`,
    prepareHeaders: (headers) => {
      const token = getAccessToken();
      headers.set('Authorization', `Bearer ${token}`);
      return headers;
    },
  }),
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
