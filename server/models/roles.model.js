import mongoose from 'mongoose';

const roleSchema = new mongoose.Schema({
  name: String,
  value: {
    type: Number,
    default: 0,
  },
});

export const roleModel = mongoose.model('roles', roleSchema);
