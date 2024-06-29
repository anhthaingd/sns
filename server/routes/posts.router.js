import { Router, json } from 'express';
import { auth } from '../middleware/auth.js';
import { uploadFields } from '../middleware/upload.js';
import {
  bookMarkPost,
  createPost,
  deleteCommentPost,
  deletePost,
  deletePostByAdmin,
  getAllPosts,
  getBookMark,
  getPostDetails,
  getPostFromAnotherUser,
  getPostsByAdmin,
  getPostsByUser,
  getPostsInChannel,
  likePost,
  postCommentPost,
  updatedPost,
} from '../controllers/posts.controllers.js';
export const router_post = Router();
router_post.use(json());
router_post.route('/api/posts').get(auth, getAllPosts);
router_post.route('/api/posts/get_by_users').get(auth, getPostsByUser);
router_post.route('/api/posts/get_by_admin').get(auth, getPostsByAdmin);
router_post
  .route('/api/posts/get_from_another_users/:id')
  .get(auth, getPostFromAnotherUser);
router_post.route('/api/posts/get_book_marked').get(auth, getBookMark);
router_post
  .route('/api/posts/get_post_details_in_channel/:id')
  .get(auth, getPostDetails);
router_post
  .route('/api/posts/:channelId')
  .get(auth, getPostsInChannel)
  .post(auth, uploadFields, createPost);
router_post
  .route('/api/posts/:channelId/:postId')
  .put(auth, uploadFields, updatedPost)
  .delete(auth, deletePost);
router_post
  .route('/api/delete_post_by_admin/:channelId/:postId')
  .delete(auth, deletePostByAdmin);
router_post
  .route('/api/posts/:channelId/:postId/like_post')
  .post(auth, likePost);
router_post
  .route('/api/posts/:channelId/:postId/book_mark')
  .post(auth, bookMarkPost);
router_post
  .route('/api/posts/:channelId/:postId/comments')
  .post(auth, postCommentPost)
  .delete(auth, deleteCommentPost);
