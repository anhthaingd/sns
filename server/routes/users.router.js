import { Router, json } from 'express';
import { auth } from '../middleware/auth.js';
import { uploadFields } from '../middleware/upload.js';
import {
  followingUser,
  getFollowers,
  getFollowing,
  getResume,
  // getFollowers,
  // getFollowing,
  getUserByToken,
  getUserDetails,
  getUsersByAdmin,
  loginUser,
  logoutUser,
  postResume,
  registerUser,
  removeFollowers,
  removeFollowing,
  searchUsers,
  updateUser,
} from '../controllers/users.controllers.js';
export const router_user = Router();
router_user.use(json());
router_user.route('/api/users/getByToken').get(auth, getUserByToken);
router_user.route('/api/users/login').post(loginUser);
router_user.route('/api/users/register').post(registerUser);
router_user.route('/api/users/logout').post(logoutUser);
router_user
  .route('/api/users/:id')
  .get(getUserDetails)
  .put(auth, uploadFields, updateUser);
router_user.route('/api/users/:id/following').post(auth, followingUser);
router_user.route('/api/users').get(auth, searchUsers);
router_user.route('/api/get_users_by_admin').get(auth, getUsersByAdmin);
router_user.route('/api/get_following').get(auth, getFollowing);
router_user.route('/api/get_followers').get(auth, getFollowers);
router_user.route('/api/remove_following/:id').delete(auth, removeFollowing);
router_user.route('/api/remove_followers/:id').delete(auth, removeFollowers);
router_user
  .route('/api/resume')
  .get(auth, getResume)
  .post(auth, uploadFields, postResume);
