import { api } from './baseApi';

// Gợi ý công ty phù hợp và phân tích thiếu sót của CV.
export const matchApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getMatchedCompanies: builder.query({
      query: (search) => `match/companies?${search}`,
      providesTags: ['matches'],
    }),
    getMatchedJobs: builder.query({
      query: (search) => `match/jobs?${search}`,
      providesTags: ['matches'],
    }),
    getJobGap: builder.query({
      query: (id) => `match/jobs/${id}/gap`,
      providesTags: ['matches'],
    }),
    getCompanyGap: builder.query({
      query: (id) => `match/companies/${id}/gap`,
      providesTags: ['matches'],
    }),
  }),
});

export const {
  useGetMatchedCompaniesQuery,
  useGetMatchedJobsQuery,
  useGetJobGapQuery,
  useGetCompanyGapQuery,
} = matchApi;
