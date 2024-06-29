import mongoose from 'mongoose';
const chatSchema = new mongoose.Schema({
  sender: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'users',
    required: true,
  },
  receiver: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'users',
    required: true,
  },
  content: { type: String, required: true },
  timestamp: { type: Date, default: Date.now },
  read_at: {
    type: Date,
    default: null,
  },
});
chatSchema.indexes({ sender: 1, receiver: 1 });
export const chatModel = mongoose.model('chats', chatSchema);
