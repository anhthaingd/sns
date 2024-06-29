import mongoose from 'mongoose';

const channelSchema = new mongoose.Schema({
  name: {
    type: String,
    unique: true,
  },
  intro: String,
  background:
    {
      name: String,
      url: String,
    } || null,
  members:
    [
      {
        type: mongoose.SchemaTypes.ObjectId,
        ref: 'users',
      },
    ] || [],
  created_at: {
    type: Date,
    default: () => Date.now(),
  },
});

channelSchema.indexes({ name: 1 });

export const channelModel = mongoose.model('channels', channelSchema);
