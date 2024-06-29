import mongoose from 'mongoose';

const notificationSchema = new mongoose.Schema({
  user: {
    type: mongoose.SchemaTypes.ObjectId,
    ref: 'users',
  },
  seeder: {
    type: mongoose.SchemaTypes.ObjectId,
    ref: 'users',
  },
  notification: String,
  url: String || null,
  created_at: {
    type: Date,
    default: () => Date.now(),
  },
  isRead: {
    type: Boolean,
    default: false,
  },
});
notificationSchema.indexes({ user: 1 });
export const notificationModel = mongoose.model(
  'notifications',
  notificationSchema
);
