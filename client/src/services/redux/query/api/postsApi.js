import { api } from './baseApi';

/**
 * Bài viết, thích, bình luận, lưu bài.
 *
 * Về cách đánh tag cache — đây là chỗ khác nhiều nhất so với bản cũ:
 *
 * Trước đây cả 7 truy vấn danh sách bài viết đều dùng chung đúng một tag
 * `'posts'`, và mọi mutation (thích, bình luận, lưu bài) đều `invalidatesTags:
 * ['posts']`. Hệ quả: bấm thích MỘT bài ở trang chủ khiến RTK Query tải lại
 * TẤT CẢ danh sách đang mở — feed, trang cá nhân, danh sách của admin, bài
 * trong channel, mục đã lưu — kể cả những danh sách không hề chứa bài đó.
 *
 * Giờ mỗi danh sách khai báo hai loại tag: một tag `LIST` cho "tập hợp này" và
 * một tag riêng cho từng bài trong đó. Mutation trên một bài chỉ vô hiệu hoá
 * tag của đúng bài ấy, nên chỉ những danh sách THẬT SỰ chứa bài đó mới tải
 * lại. Thêm/xoá bài mới đụng tới tag `LIST`.
 */

const LIST = { type: 'posts', id: 'LIST' };

/** Tag cho một truy vấn trả về danh sách bài viết. */
const listTags = (result) => [
  LIST,
  ...(result?.posts || []).map((post) => ({ type: 'posts', id: post._id })),
];

/** Tag của đúng một bài — dùng cho mutation nhận `{ postId }`. */
const onePost = (result, error, arg) => [{ type: 'posts', id: arg?.postId }];

export const postsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getPosts: builder.query({
      query: (search) => `posts?${search}`,
      providesTags: listTags,
    }),
    getPostDetails: builder.query({
      query: (id) => `posts/get_post_details_in_channel/${id}`,
      providesTags: (result, error, id) => [{ type: 'posts', id }],
    }),
    getPostsByUser: builder.query({
      query: (search) => `posts/get_by_users?${search}`,
      providesTags: listTags,
    }),
    getPostsByAdmin: builder.query({
      query: (search) => `posts/get_by_admin?${search}`,
      providesTags: listTags,
    }),
    getPostsInChannel: builder.query({
      query: ({ channelId, search }) => `posts/${channelId}?${search}`,
      providesTags: listTags,
    }),
    getPostsFromAnotherUser: builder.query({
      query: ({ id, search }) => ({
        url: `posts/get_from_another_users/${id}?${search}`,
      }),
      providesTags: listTags,
    }),
    getBookMarks: builder.query({
      query: (search) => `posts/get_book_marked?${search}`,
      providesTags: (result) => [
        { type: 'bookmarks', id: 'LIST' },
        ...(result?.posts || []).map((post) => ({ type: 'posts', id: post._id })),
      ],
    }),

    createPost: builder.mutation({
      query: ({ channelId, body }) => ({
        url: `posts/${channelId}`,
        method: 'POST',
        body: body,
      }),
      // Bài mới -> mọi danh sách phải tải lại, chưa có tag riêng để nhắm.
      invalidatesTags: [LIST],
    }),
    updatePost: builder.mutation({
      query: ({ channelId, postId, body }) => ({
        url: `posts/${channelId}/${postId}`,
        method: 'PUT',
        body: body,
      }),
      invalidatesTags: onePost,
    }),
    deletePost: builder.mutation({
      query: ({ channelId, postId }) => ({
        url: `posts/${channelId}/${postId}`,
        method: 'DELETE',
      }),
      // Xoá thì độ dài danh sách đổi -> phải đụng cả tag LIST.
      invalidatesTags: (result, error, arg) => [LIST, { type: 'posts', id: arg?.postId }],
    }),
    deletePostByAdmin: builder.mutation({
      query: ({ channelId, postId }) => ({
        url: `delete_post_by_admin/${channelId}/${postId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, arg) => [LIST, { type: 'posts', id: arg?.postId }],
    }),
    likePost: builder.mutation({
      query: ({ channelId, postId }) => ({
        url: `posts/${channelId}/${postId}/like_post`,
        method: 'POST',
      }),
      invalidatesTags: onePost,
    }),
    bookMarkPost: builder.mutation({
      query: ({ channelId, postId }) => ({
        url: `posts/${channelId}/${postId}/book_mark`,
        method: 'POST',
      }),
      // Lưu/bỏ lưu làm đổi cả bài đó lẫn danh sách "đã lưu".
      invalidatesTags: (result, error, arg) => [
        { type: 'posts', id: arg?.postId },
        { type: 'bookmarks', id: 'LIST' },
      ],
    }),
    commentPost: builder.mutation({
      query: ({ channelId, postId, content }) => ({
        url: `posts/${channelId}/${postId}/comments`,
        method: 'POST',
        body: {
          content: content,
        },
      }),
      invalidatesTags: onePost,
    }),
    deleteCommentPost: builder.mutation({
      query: ({ channelId, postId, commentId }) => ({
        url: `posts/${channelId}/${postId}/comments`,
        method: 'DELETE',
        body: { commentId: commentId },
      }),
      invalidatesTags: onePost,
    }),
  }),
});

export const {
  useGetPostsQuery,
  useGetPostDetailsQuery,
  useGetPostsByUserQuery,
  useGetPostsByAdminQuery,
  useGetPostsInChannelQuery,
  useGetPostsFromAnotherUserQuery,
  useGetBookMarksQuery,
  useCreatePostMutation,
  useUpdatePostMutation,
  useDeletePostMutation,
  useDeletePostByAdminMutation,
  useLikePostMutation,
  useBookMarkPostMutation,
  useCommentPostMutation,
  useDeleteCommentPostMutation,
} = postsApi;
