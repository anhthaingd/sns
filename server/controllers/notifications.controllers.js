import { notificationModel } from '../models/notifications.model.js';

export const getNotifications = async (req, res) => {
  const user = req.decoded;
  const { page } = req.query;
  const curPage = page ? Number(page) : 1;
  try {
    const [totalNotifications, totalNotificationsNotRead, notifications] =
      await Promise.all([
        notificationModel.countDocuments({
          user: user._id,
        }),
        notificationModel.countDocuments({
          user: user._id,
          isRead: false,
        }),
        notificationModel
          .find({ user: user._id })
          .skip((curPage - 1) * 10)
          .limit(10)
          .sort({ created_at: -1 })
          .populate('seeder', '_id username email avatar'),
      ]);
    return res.status(200).json({
      error: false,
      success: true,
      notifications: notifications,
      notRead: totalNotificationsNotRead,
      totalPage: Math.ceil(totalNotifications / 10),
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const readNotification = async (req, res) => {
  const user = req.decoded;
  const { id } = req.params;
  try {
    const updatedNotification = await notificationModel.findOneAndUpdate(
      { _id: id, user: user._id },
      { isRead: true }
    );
    if (updatedNotification)
      return res.status(200).json({ error: false, success: true });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
