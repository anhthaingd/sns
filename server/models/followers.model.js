import mongoose from 'mongoose';

const followerSchema = new mongoose.Schema({
  user: {
    type: mongoose.SchemaTypes.ObjectId,
    ref: 'users',
  },
  followers:
    [
      {
        type: mongoose.SchemaTypes.ObjectId,
        ref: 'users',
      },
    ] || [],
});

followerSchema.indexes({ user: 1 });
export const followerModel = mongoose.model('followers', followerSchema);
