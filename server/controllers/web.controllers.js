import { webModel } from '../models/web.model.js';
import { deleteFile } from '../utils/deleteFile.js';

export const getWeb = async (req, res) => {
  try {
    const website = await webModel.find();
    if (website)
      return res
        .status(200)
        .json({ error: false, success: true, website: website[0] });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const updateWeb = async (req, res) => {
  const user = req.decoded;
  const { id } = req.params;
  const {
    oldLogo,
    website_name,
    color_title,
    website_quotes_register,
    website_quotes_login,
  } = req.body;
  const files = req.files;
  const parseOldLogo = oldLogo ? JSON.parse(oldLogo) : null;
  try {
    if (user?.role?.value !== 1)
      return res.status(403).json({
        error: true,
        success: false,
        message: 'Chức năng này chỉ dành cho admin!',
      });
    const web = {
      website_name: website_name,
      color_title: color_title,
      website_quotes_register: website_quotes_register,
      website_quotes_login: website_quotes_login,
    };
    if (files.images && files?.images[0]) {
      if (parseOldLogo?.name !== 'vite.svg') {
        await deleteFile(parseOldLogo?.url || '');
      }
      web.logo = {
        name: files?.images[0]?.filename,
        url: files?.images[0]?.path,
      };
    }
    const updatedWeb = await webModel.findByIdAndUpdate(
      id,
      { ...web },
      { new: true }
    );
    if (updatedWeb)
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Cập nhật thông tin website thành công!',
      });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
