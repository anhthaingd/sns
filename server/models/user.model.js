import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
  username: String,
  email: String,
  password: String,
  address: String,
  intro: String,
  cover_bg: {
    name: {
      type: String,
      default: '',
    },
    url: {
      type: String,
      default: '',
    },
  },
  avatar: {
    name: {
      type: String,
      default: 'avatar_trang.jpg',
    },
    url: {
      type: String,
      default: 'public/avatar-trang.jpg',
    },
  },
  created_at: {
    type: Date,
    default: () => Date.now(),
  },
  updated_at: {
    type: Date,
    default: () => Date.now(),
  },
  role: {
    type: mongoose.SchemaTypes.ObjectId,
    ref: 'roles',
  },
  socketId: String || null,
  socketCallId: String || null,
});

userSchema.indexes({ email: 1 });

export const userModel = mongoose.model('users', userSchema);
