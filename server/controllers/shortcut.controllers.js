import { channelModel } from '../models/channels.model.js';
import { shortCutModel } from '../models/shortcut.model.js';

export const getShortcuts = async (req, res) => {
  const user = req.decoded;
  try {
    const shortcuts = await shortCutModel
      .find({ user: user._id, isJoin: true })
      .populate('channel', '_id name background')
      .sort({ count: 1 });
    // .limit(8);
    return res
      .status(200)
      .json({ error: false, success: true, shortcuts: shortcuts });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const updateShortcut = async (req, res) => {
  const user = req.decoded;
  const { id } = req.params;
  try {
    const isJoinChannel = await channelModel.findOne({ members: user._id });
    if (isJoinChannel) {
      const existed = await shortCutModel.findOne({
        user: user._id,
        channel: id,
      });
      if (existed) {
        const updated = await shortCutModel.findOneAndUpdate(
          { user: user._id, channel: id },
          {
            $inc: {
              count: 1,
            },
          }
        );
        if (updated)
          return res.status(200).json({ error: false, success: true });
      }
      const created = await shortCutModel.create({
        user: user._id,
        channel: id,
        count: 1,
        isJoin: true,
      });
      if (created) return res.status(200).json({ error: false, success: true });
    }
    return res.status(403).json({
      error: true,
      success: false,
      message: 'Bạn chưa gia nhập channel này!',
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
