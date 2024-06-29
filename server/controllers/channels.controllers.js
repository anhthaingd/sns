import { channelModel } from '../models/channels.model.js';
import { notificationModel } from '../models/notifications.model.js';
import { postModel } from '../models/post.model.js';
import { shortCutModel } from '../models/shortcut.model.js';
import { userModel } from '../models/user.model.js';
import { deleteFile } from '../utils/deleteFile.js';
import unidecode from 'unidecode';
export const getAllChannels = async (req, res) => {
  const { page, search } = req.query;
  const curPage = page ? Number(page) : 1;
  const query = {};
  try {
    if (
      search &&
      search !== 'null' &&
      search !== null &&
      search.trim() !== ''
    ) {
      const unaccentedQueryString = unidecode(search);
      const regex = new RegExp(unaccentedQueryString, 'i');
      query.name = regex;
    }
    const totalChannels = await channelModel.countDocuments(query);
    const channels = await channelModel
      .find(query)
      .populate('members', '_id username email avatar role')
      .populate({
        path: 'members',
        populate: {
          path: 'role',
          select: '_id name',
        },
      })
      .sort({ created_at: -1 })
      .skip((curPage - 1) * 10)
      .limit(10);
    return res.status(200).json({
      error: false,
      success: true,
      channels: channels,
      totalPage: Math.ceil(totalChannels / 10),
      curPage: Number(curPage),
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const getChannelsByUser = async (req, res) => {
  const user = req.decoded;
  try {
    const channels = await channelModel.find({ members: user._id }).populate({
      path: 'members',
      select: '_id username email avatar role',
      populate: {
        path: 'role',
        select: '_id name value',
      },
    });
    return res
      .status(200)
      .json({ error: false, success: true, channels: channels });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const getChannelDetails = async (req, res) => {
  const user = req.decoded;
  const { id } = req.params;
  try {
    const existedChannel = await channelModel
      .findOne({ _id: id, members: user._id })
      .populate({
        path: 'members',
        select: '_id username email avatar role',
        populate: {
          path: 'role',
          select: '_id name value',
        },
      });
    if (existedChannel) {
      // if (existedChannel.members?.map((m) => m._id).includes(user._id))
      return res
        .status(200)
        .json({ error: false, success: true, channel: existedChannel });
    }
    return res.status(403).json({
      error: true,
      success: false,
      message: 'Bạn chưa tham gia channel này!',
    });
    // return res.status(404).json({
    //   error: true,
    //   success: false,
    //   message: 'Không tìm thấy channel!',
    // });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const createChannel = async (req, res) => {
  const user = req.decoded;
  const { name, intro } = req.body;
  const files = req.files;
  try {
    if (user?.role?.value !== 1)
      return res.status(403).json({
        error: true,
        success: false,
        message: 'Chức năng này chỉ dành cho admin!',
      });
    const channel = {
      name: name,
      intro: intro,
      members: [user._id],
    };
    const existedChannel = await channelModel.findOne({ name: channel.name });
    if (existedChannel) {
      await deleteFile(files.images[0].url || '');
      return res
        .status(409)
        .json({ error: true, success: false, message: 'Channel đã tồn tại!' });
    }
    if (files.images[0]) {
      channel.background = {
        name: files.images[0].filename,
        url: files.images[0].path,
      };
    }
    const createdChannel = await channelModel.create(channel);
    if (createdChannel)
      return res.status(201).json({
        error: false,
        success: true,
        message: 'Tạo channel thành công!',
      });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const joinChannel = async (req, res) => {
  const user = req.decoded;
  const { id } = req.params;
  try {
    if (user?.role?.value === 1)
      return res.status(403).json({
        error: true,
        success: false,
        message: 'Admin không thể tự ý rời khỏi nhóm!',
      });

    const existedChannel = await channelModel.findById(id);
    if (!existedChannel)
      return res.status(404).json({
        error: true,
        success: false,
        message: 'Channel không tồn tại!',
      });

    const existedShortCut = await shortCutModel.findOne({
      user: user._id,
      channel: id,
    });

    if (!existedShortCut) {
      await shortCutModel.create({ channel: id, user: user._id, isJoin: true });
    }

    if (existedChannel.members.includes(user._id)) {
      const updatedChannel = await channelModel.findByIdAndUpdate(id, {
        $pull: {
          members: user._id,
        },
      });

      if (updatedChannel) {
        await shortCutModel.findOneAndDelete({
          user: user._id,
          channel: updatedChannel._id,
        });

        return res.status(200).json({
          error: false,
          success: true,
          message: 'Bạn đã thoát nhóm channel!',
        });
      }
    }

    const updatedChannel = await channelModel.findByIdAndUpdate(
      id,
      {
        $push: {
          members: user._id,
        },
      },
      { new: true }
    );

    await shortCutModel.findOneAndUpdate(
      { user: user._id, channel: id },
      { isJoin: true }
    );

    if (updatedChannel) {
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Gia nhập channel thành công!',
      });
    }
  } catch (error) {
    return res.status(500).json({
      error: true,
      success: false,
      message: error.message,
    });
  }
};

export const removeUserFromChannel = async (req, res) => {
  const user = req.decoded;
  const { id } = req.params;
  const { userId } = req.body;
  try {
    if (user?.role?.value !== 1)
      return res.status(403).json({
        error: true,
        success: false,
        message: 'Chức năng này chỉ dành cho admin!',
      });
    if (userId === user._id)
      return res.status(409).json({
        error: true,
        success: false,
        message: 'Bạn không thể xóa chính mình ra khỏi channel!',
      });
    const isAdmin = await userModel.findOne({ _id: userId }).populate('role');
    if (isAdmin && isAdmin.role?.value === 1)
      return res.status(403).json({
        error: true,
        success: false,
        message: 'Bạn không thể xóa admin khác ra khỏi nhóm!',
      });
    const [updatedChannel, _] = await Promise.all([
      channelModel.findByIdAndUpdate(id, {
        $pull: {
          members: userId,
        },
      }),
      shortCutModel.findOneAndUpdate(
        { user: userId, channel: id },
        { isJoin: false }
      ),
    ]);
    if (updatedChannel) {
      await notificationModel.create({
        user: userId,
        seeder: user._id,
        notification: `Admin đã xóa bạn ra khỏi channel ${updatedChannel.name}!`,
        url: null,
      });
      return res.status(200).json({
        error: false,
        success: true,
        message: `Đã xóa người dùng id:${userId} ra khỏi channel!`,
      });
    }
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const updatedChannel = async (req, res) => {
  const user = req.decoded;
  const { name, intro, oldBackground } = req.body;
  const { id } = req.params;
  const files = req.files;
  const parseOldImage = oldBackground ? JSON.parse(oldBackground) : null;
  try {
    if (user?.role?.value !== 1)
      return res.status(403).json({
        error: true,
        success: false,
        message: 'Chức năng này chỉ dành cho admin!',
      });
    const channel = {
      name: name,
      intro: intro,
    };
    if (files.images && files?.images[0]) {
      if (parseOldImage !== null) {
        await deleteFile(parseOldImage.url);
      }
      channel.background = {
        name: files?.images[0]?.filename,
        url: files?.images[0]?.path,
      };
    }
    const updatedChannel = await channelModel.findByIdAndUpdate(id, {
      ...channel,
    });
    if (updatedChannel)
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Cập nhật channel thành công!',
      });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const deleteChannel = async (req, res) => {
  const user = req.decoded;
  const { id } = req.params;
  try {
    if (user?.role?.value !== 1)
      return res.status(403).json({
        error: true,
        success: false,
        message: 'Chức năng này chỉ dành cho admin!',
      });
    const [deletedChannel, _, __] = await Promise.all([
      channelModel.findByIdAndDelete(id),
      postModel.deleteMany({ channel: id }),
      shortCutModel.findOneAndUpdate({ channel: id }, { isJoin: false }),
    ]);
    if (deletedChannel) {
      await deleteFile(deletedChannel.background?.url);
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Xóa channel thành công!',
      });
    }
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
