import { Router, json } from 'express';
import { auth } from '../middleware/auth.js';
import {
  getShortcuts,
  updateShortcut,
} from '../controllers/shortcut.controllers.js';
export const router_shortcut = Router();
router_shortcut.use(json());
router_shortcut.route('/api/shortcuts').get(auth, getShortcuts);
router_shortcut.route('/api/shortcuts/:id').put(auth, updateShortcut);
