import { api } from './baseApi';

// CV của người dùng.
export const resumeApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getResume: builder.query({
      query: () => 'resume',
      providesTags: ['resume'],
    }),
    getResumeAdvice: builder.query({
      query: ({ lang }) => `resume/advice?lang=${lang}`,
      providesTags: ['resume'],
    }),
    postResume: builder.mutation({
      query: (body) => ({
        url: 'resume',
        method: 'POST',
        body: body,
      }),
      // Sua CV thi ket qua goi y cong ty phai tinh lai.
      invalidatesTags: ['resume', 'matches'],
    }),
  }),
});

export const {
  useGetResumeQuery,
  useGetResumeAdviceQuery,
  usePostResumeMutation,
} = resumeApi;
