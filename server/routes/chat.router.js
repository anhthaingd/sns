import { Router, json } from 'express';
import { auth } from '../middleware/auth.js';
import {
  getChat,
  getNewestMessage,
  readMessage,
} from '../controllers/chat.controllers.js';
export const router_chat = Router();
router_chat.use(json());
router_chat.route('/api/messages/:senderId/:receiverId').get(auth, getChat);
router_chat.route('/api/newest_messages').get(auth, getNewestMessage);
router_chat.route('/api/newest_messages/:id').put(auth, readMessage);
