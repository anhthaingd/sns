import mongoose from 'mongoose';

const shortcutSchema = new mongoose.Schema({
  channel: {
    type: mongoose.SchemaTypes.ObjectId,
    ref: 'channels',
  },
  user: {
    type: mongoose.SchemaTypes.ObjectId,
    ref: 'users',
  },
  count: {
    type: Number,
    default: 0,
  },
  isJoin: {
    type: Boolean,
    default: false,
  },
});

shortcutSchema.indexes({ channel: 1 });
shortcutSchema.indexes({ user: 1 });
shortcutSchema.indexes({ channel: 1, user: 1 });

export const shortCutModel = mongoose.model('shortcuts', shortcutSchema);
