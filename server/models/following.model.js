import mongoose from 'mongoose';
const followingSchema = new mongoose.Schema({
  user: {
    type: mongoose.SchemaTypes.ObjectId,
    ref: 'users',
  },
  following:
    [
      {
        type: mongoose.SchemaTypes.ObjectId,
        ref: 'users',
      },
    ] || [],
});

followingSchema.indexes({ user: 1 });
export const followingModel = mongoose.model('followings', followingSchema);
