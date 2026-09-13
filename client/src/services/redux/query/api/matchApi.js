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
    getWhatIf: builder.query({
      query: () => 'match/whatif',
      providesTags: ['matches'],
    }),
    // Lời khuyên do LLM viết — endpoint RIÊNG, gọi sau khi trang đã vẽ xong.
    // Gộp vào endpoint gap thì một màn hình 15ms thành một màn hình 5 giây.
    getOverviewAdvice: builder.query({
      query: ({ page = 1, lang }) => `match/advice/overview?page=${page}&lang=${lang}`,
      providesTags: ['matches'],
    }),
    getJobAdvice: builder.query({
      query: ({ id, lang }) => `match/jobs/${id}/advice?lang=${lang}`,
      providesTags: ['matches'],
    }),
    getCompanyAdvice: builder.query({
      query: ({ id, lang }) => `match/companies/${id}/advice?lang=${lang}`,
      providesTags: ['matches'],
    }),
    getWhatIfAdvice: builder.query({
      query: ({ lang }) => `match/whatif/advice?lang=${lang}`,
      providesTags: ['matches'],
    }),
    simulateWhatIf: builder.mutation({
      query: (actions) => ({
        url: 'match/whatif',
        method: 'POST',
        body: { actions },
      }),
    }),
  }),
});

export const {
  useGetMatchedCompaniesQuery,
  useGetMatchedJobsQuery,
  useGetJobGapQuery,
  useGetCompanyGapQuery,
  useGetWhatIfQuery,
  useGetOverviewAdviceQuery,
  useGetJobAdviceQuery,
  useGetCompanyAdviceQuery,
  useGetWhatIfAdviceQuery,
  useSimulateWhatIfMutation,
} = matchApi;
