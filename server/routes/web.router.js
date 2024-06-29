import { Router, json } from 'express';
import { auth } from '../middleware/auth.js';
import { getWeb, updateWeb } from '../controllers/web.controllers.js';
import { uploadFields } from '../middleware/upload.js';
export const router_web = Router();
router_web.use(json());
router_web.route('/api/website').get(getWeb);
router_web.route('/api/website/:id').put(auth, uploadFields, updateWeb);
