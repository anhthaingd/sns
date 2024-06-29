import mongoose from 'mongoose';

const newestMessage = new mongoose.Schema({
  sender: {
    user: {
      type: mongoose.SchemaTypes.ObjectId,
      ref: 'users',
    },
    isRead: {
      type: Boolean,
      default: false,
    },
  },
  receiver: {
    user: {
      type: mongoose.SchemaTypes.ObjectId,
      ref: 'users',
    },
    isRead: {
      type: Boolean,
      default: false,
    },
  },
  content: String,
  lastSent: {
    type: mongoose.SchemaTypes.ObjectId,
    ref: 'users',
  },
  updated_at: {
    type: Date,
    default: () => Date.now(),
  },
});

export const newestMessageModel = mongoose.model(
  'newestmessages',
  newestMessage
);
