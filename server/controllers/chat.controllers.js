import { chatModel } from '../models/chat.model.js';
import { newestMessageModel } from '../models/newestMessage.model.js';

export const getChat = async (req, res) => {
  const { senderId, receiverId } = req.params;
  const { page } = req.query;
  const curPage = page ? Number(page) : 1;
  try {
    const totalMessages = await chatModel.countDocuments({
      $or: [
        { sender: senderId, receiver: receiverId },
        { sender: receiverId, receiver: senderId },
      ],
    });
    const messages = await chatModel
      .find({
        $or: [
          { sender: senderId, receiver: receiverId },
          { sender: receiverId, receiver: senderId },
        ],
      })
      .populate('sender', '_id username email avatar cover_bg')
      .populate('receiver', '_id username email avatar cover_bg')
      .sort({ timestamp: -1 });
    // .skip((curPage - 1) * 20)
    // .limit(20);
    return res.status(200).json({
      error: false,
      success: true,
      messages: messages,
      totalPage: Math.ceil(totalMessages / 20),
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const postChat = async (req, res) => {
  const { sender, recipient, content } = req.body;
  try {
    const newMessage = new chatModel({ sender, recipient, content });
    await newMessage.save();
    res
      .status(201)
      .json({ error: false, success: true, newMessage: newMessage });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const getNewestMessage = async (req, res) => {
  const user = req.decoded;
  // const { page } = req.query;
  // const curPage = page ? Number(page) : 1;
  try {
    const totalUnread = await newestMessageModel.countDocuments({
      $or: [
        {
          'sender.user': user._id,
          'sender.isRead': false,
        },
        {
          'receiver.user': user._id,
          'receiver.isRead': false,
        },
      ],
    });
    const messages = await newestMessageModel
      .find({
        $or: [
          {
            'sender.user': user._id,
          },
          {
            'receiver.user': user._id,
          },
        ],
      })
      .sort({ updated_at: -1 })
      .populate('sender.user', '_id username email avatar cover_bg')
      .populate('receiver.user', '_id username email avatar cover_bg')
      .lean();
    // .skip((curPage - 1) * 10)
    // .limit(10);
    return res.status(200).json({
      error: false,
      success: true,
      messages: messages,
      unread: totalUnread,
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const readMessage = async (req, res) => {
  const user = req.decoded;
  const { id } = req.params;
  try {
    const curMessage = await newestMessageModel.findOne({
      _id: id,
      $or: [
        {
          'sender.user': user._id,
        },
        {
          'receiver.user': user._id,
        },
      ],
    });
    if (curMessage?.sender?.user?.toString() === user._id) {
      curMessage.sender.isRead = true;
      await curMessage.save();
      return res.status(200).json({ error: false, success: true });
    }
    if (curMessage?.receiver?.user?.toString() === user._id) {
      curMessage.receiver.isRead = true;
      await curMessage.save();
      return res.status(200).json({ error: false, success: true });
    }
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
