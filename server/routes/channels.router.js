import { Router, json } from 'express';
import {
  createChannel,
  deleteChannel,
  getAllChannels,
  getChannelDetails,
  getChannelsByUser,
  joinChannel,
  removeUserFromChannel,
  updatedChannel,
} from '../controllers/channels.controllers.js';
import { auth } from '../middleware/auth.js';
import { uploadFields } from '../middleware/upload.js';
export const router_channel = Router();
router_channel.use(json());
router_channel
  .route('/api/channels')
  .get(getAllChannels)
  .post(auth, uploadFields, createChannel);
router_channel.route('/api/channels/get_by_user').get(auth, getChannelsByUser);
router_channel
  .route('/api/channels/:id')
  .get(auth, getChannelDetails)
  .post(auth, joinChannel)
  .put(auth, uploadFields, updatedChannel)
  .delete(auth, deleteChannel);
router_channel
  .route('/api/channels/:id/delete_user')
  .delete(auth, removeUserFromChannel);
