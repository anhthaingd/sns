import jwt from 'jsonwebtoken';
export const signToken = async (data, expiresIn = '7d') => {
  return jwt.sign(data, process.env.ACCESS_TOKEN_SECRET, {
    expiresIn: expiresIn,
  });
};
