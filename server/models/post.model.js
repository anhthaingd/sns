import mongoose from 'mongoose';
const postSchema = new mongoose.Schema({
  user: {
    type: mongoose.SchemaTypes.ObjectId,
    ref: 'users',
  },
  content: String,
  images: {
    name: String,
    url: String,
  },
  created_at: {
    type: Date,
    default: () => Date.now(),
  },
  updated_at: {
    type: Date,
    default: () => Date.now(),
  },
  liked: [
    {
      type: mongoose.SchemaTypes.ObjectId,
      ref: 'users',
    },
  ],
  book_marked: [
    {
      type: mongoose.SchemaTypes.ObjectId,
      ref: 'users',
    },
  ],
  comments: [
    {
      user: { type: mongoose.SchemaTypes.ObjectId, ref: 'users' },
      content: String,
      created_at: {
        type: Date,
        default: () => Date.now(),
      },
    },
  ],
  channel: {
    type: mongoose.SchemaTypes.ObjectId,
    ref: 'channels',
  },
});
postSchema.indexes({ user: 1 });
postSchema.indexes({ channel: 1 });
postSchema.pre('findOneAndUpdate', function (next) {
  if (this.comments && this.comments.length > 1) {
    this.comments.sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    );
  }
  next();
});

export const postModel = mongoose.model('posts', postSchema);
