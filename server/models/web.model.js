import mongoose from 'mongoose';
const webSchema = new mongoose.Schema({
  logo: {
    name: String,
    url: String,
  },
  website_name: String,
  website_quotes_register: String,
  website_quotes_login: String,
  color_title: String,
});
export const webModel = mongoose.model('webs', webSchema);
