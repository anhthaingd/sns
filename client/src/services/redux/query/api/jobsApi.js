import { api } from './baseApi';

// Việc làm và doanh nghiệp đã qua ETL.
export const jobsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getJobs: builder.query({
      query: (search) => `jobs?${search}`,
      providesTags: ['jobs'],
    }),
    getJobFilters: builder.query({
      query: () => 'jobs/filters',
      providesTags: ['jobs'],
    }),
    getJobDetails: builder.query({
      query: (id) => `jobs/${id}`,
    }),
    getCompanies: builder.query({
      query: (search) => `companies?${search}`,
      providesTags: ['companies'],
    }),
    getCompanyDetails: builder.query({
      query: (id) => `companies/${id}`,
    }),
  }),
});

export const {
  useGetJobsQuery,
  useGetJobFiltersQuery,
  useGetJobDetailsQuery,
  useGetCompaniesQuery,
  useGetCompanyDetailsQuery,
} = jobsApi;
