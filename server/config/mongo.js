import mongoose from 'mongoose';

export const connectDb = async () => {
  try {
    const options = {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      minPoolSize: 1,
      maxPoolSize: 50,
    };
    await mongoose.connect(process.env.DATABASE_URL, options);

    console.log('MongoDB connected!');
  } catch (error) {
    console.error('Error connecting to MongoDB:', error);
    throw error;
  }
};
