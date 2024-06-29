import { Router, json } from 'express';
import { auth } from '../middleware/auth.js';
import {
  getNotifications,
  readNotification,
} from '../controllers/notifications.controllers.js';
export const router_notifications = Router();
router_notifications.use(json());
router_notifications.route('/api/notifications').get(auth, getNotifications);
router_notifications
  .route('/api/notifications/:id')
  .post(auth, readNotification);
