import mongoose from 'mongoose';
const resumeSchema = new mongoose.Schema({
  user: {
    type: mongoose.SchemaTypes.ObjectId,
    ref: 'users',
  },
  name: String,
  avatar: {
    name: String,
    url: String,
  },
  position: String,
  birthday: String,
  email: String,
  address: String,
  phone: String,
  github: String,
  objective: String,
  educationName: String,
  educationMajor: String,
  educationCompletion: String,
  educationGPA: String,
  experiences: [
    {
      name: String,
      startTime: String,
      endTime: String,
      position: String,
      description: String,
    },
  ],
  skills: [String],
  languages: [String],
  projects: [
    {
      name: String,
      tech: String,
      description: String,
    },
  ],
  certificates: [
    {
      name: String,
      url: String,
    },
  ],
});
resumeSchema.indexes({ user: 1 });
export const resumeModel = mongoose.model('resumes', resumeSchema);
