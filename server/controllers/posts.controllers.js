import { channelModel } from '../models/channels.model.js';
import { userModel } from '../models/user.model.js';
import { notificationModel } from '../models/notifications.model.js';
import { postModel } from '../models/post.model.js';
import { deleteFile } from '../utils/deleteFile.js';
export const getAllPosts = async (req, res) => {
  const user = req.decoded;
  const { page, search } = req.query;
  const curPage = page ? Number(page) : 1;
  let query = {};

  try {
    const channels = await channelModel.find({ members: user._id });
    const channelsId = channels.map((channel) => channel._id);
    if (search) {
      const regex = { $regex: search, $options: 'i' };
      const [searchUser, searchChannel] = await Promise.all([
        userModel.find({
          _id: { $ne: user._id },
          $or: [{ username: regex }, { email: regex }],
        }),
        channelModel.findOne({ name: regex }),
      ]);

      query.$or = [
        {
          user: { $in: searchUser.map((u) => u._id) || [] },
        },
        {
          channel: searchChannel?._id || null,
        },
        {
          content: regex,
        },
      ];
    }

    query.channel = { $in: channelsId };

    const totalPosts = await postModel.countDocuments(query);
    const posts = await postModel
      .find(query)
      .populate('user', '_id email username avatar')
      .populate('channel', '_id name')
      .populate('liked', '_id email username avatar')
      .populate('book_marked', '_id email username avatar')
      .populate('comments.user', '_id email username avatar')
      .sort({ created_at: -1 })
      .skip((curPage - 1) * 10)
      .limit(10);

    return res.status(200).json({
      error: false,
      success: true,
      posts: posts,
      totalPage: Math.ceil(totalPosts / 10),
      totalPosts: totalPosts,
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const getPostsByAdmin = async (req, res) => {
  const user = req.decoded;
  const { page, channel } = req.query;
  const curPage = page ? Number(page) : 1;
  let query = {};
  try {
    if (user?.role?.value !== 1)
      return res.status(403).json({
        error: true,
        success: false,
        message: 'Bạn không đủ quyền!',
      });
    if (channel && channel !== 'null' && channel !== null) {
      query.channel = channel;
    }
    const totalPosts = await postModel.countDocuments(query);
    const posts = await postModel
      .find(query)
      .populate({
        path: 'user',
        select: '_id email username avatar role',
        populate: {
          path: 'role',
          select: '_id name value',
        },
      })
      .populate('channel', '_id name')
      .populate('liked', '_id email username avatar')
      .populate('book_marked', '_id email username avatar')
      .populate('comments.user', '_id email username avatar')
      .skip((curPage - 1) * 10)
      .limit(10);
    return res.status(200).json({
      error: false,
      success: true,
      posts: posts,
      totalPage: Math.ceil(totalPosts / 10),
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const getPostsByUser = async (req, res) => {
  const user = req.decoded;
  const { page } = req.query;
  const curPage = page ? Number(page) : 1;
  try {
    const totalPosts = await postModel.countDocuments({
      user: user._id,
    });
    const posts = await postModel
      .find({ user: user._id })
      .populate('user', '_id email username avatar')
      .populate('channel', '_id name')
      .populate('liked', '_id email username avatar')
      .populate('book_marked', '_id email username avatar')
      .populate('comments.user', '_id email username avatar')
      .skip((curPage - 1) * 10)
      .limit(10);
    return res.status(200).json({
      error: false,
      success: true,
      posts: posts,
      totalPage: Math.ceil(totalPosts / 10),
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const getPostFromAnotherUser = async (req, res) => {
  const user = req.decoded;
  const { id } = req.params;
  const { page } = req.query;
  const curPage = page ? Number(page) : 1;
  try {
    const channels = await channelModel.find({ members: user._id });
    const channelsId = channels.map((channel) => channel._id);
    const totalPosts = await postModel.countDocuments({
      user: id,
      channel: { $in: channelsId },
    });
    const posts = await postModel
      .find({
        user: id,
        channel: { $in: channelsId },
      })
      .populate('user', '_id email username avatar')
      .populate('channel', '_id name')
      .populate('liked', '_id email username avatar')
      .populate('book_marked', '_id email username avatar')
      .populate('comments.user', '_id email username avatar')
      .sort({ created_at: -1 })
      .skip((curPage - 1) * 10)
      .limit(10);
    return res.status(200).json({
      error: false,
      success: true,
      posts: posts,
      totalPage: Math.ceil(totalPosts / 10),
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const getPostsInChannel = async (req, res) => {
  const { channelId } = req.params;
  const { page } = req.query;
  const curPage = page ? Number(page) : 1;
  try {
    const totalPosts = await postModel.countDocuments({
      channel: channelId,
    });
    const posts = await postModel
      .find({ channel: channelId })
      .populate('user', '_id email username avatar')
      .populate('channel', '_id name')
      .populate('liked', '_id email username avatar')
      .populate('book_marked', '_id email username avatar')
      .populate('comments.user', '_id email username avatar')
      .skip((curPage - 1) * 10)
      .limit(10)
      .sort({ updated_at: -1 });
    return res.status(200).json({
      error: false,
      success: true,
      posts: posts,
      totalPage: Math.ceil(totalPosts / 10),
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const getPostDetails = async (req, res) => {
  const { id } = req.params;
  try {
    const post = await postModel
      .findById(id)
      .populate('user', '_id email username avatar')
      .populate('channel', '_id name')
      .populate('liked', '_id email username avatar')
      .populate('book_marked', '_id email username avatar')
      .populate('comments.user', '_id email username avatar');
    if (post)
      return res.status(200).json({ error: false, success: true, post: post });
    return res.status(404).json({
      error: false,
      success: true,
      message: 'Không tìm thấy bài viết!',
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const createPost = async (req, res) => {
  const user = req.decoded;
  const { channelId } = req.params;
  const { content } = req.body;
  const files = req.files;
  try {
    if (!content || !channelId)
      return res.status(400).json({
        error: true,
        success: false,
        message: 'Yêu cầu bài viết phải có nội dung và channelId!',
      });
    const post = {
      user: user._id,
      content: content,
      channel: channelId,
    };
    if (files?.images && files.images[0]) {
      post.images = {
        name: files.images[0].filename,
        url: files.images[0].path,
      };
    }
    const createdPost = await postModel.create(post);
    if (createdPost)
      return res.status(201).json({
        error: false,
        success: true,
        message: 'Tạo bài viết thành công!',
      });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const updatedPost = async (req, res) => {
  const user = req.decoded;
  const { channelId, postId } = req.params;
  const { oldImages, content } = req.body;
  const parseJson = (jsonString) => {
    try {
      let jsonStr = jsonString ? JSON.parse(jsonString) : null;
      return jsonStr;
    } catch (error) {
      console.error('Error parsing JSON:', error);
      return null;
    }
  };
  const parseOldImages = parseJson(oldImages) || null;
  const files = req.files;
  try {
    const correctPost = await postModel.findOne({
      _id: postId,
      channel: channelId,
      user: user._id,
    });
    if (!correctPost)
      return res.status(403).json({
        error: true,
        success: false,
        message:
          'Bạn không thể sửa bài viết của người khác hoặc bài viết trong channel đã bị xóa!',
      });
    const post = {
      user: user._id,
      content: content,
      updated_at: Date.now(),
    };
    if (files.images && files.images[0]) {
      await deleteFile(parseOldImages?.url);
      post.images = {
        name: files.images[0].filename,
        url: files.images[0].path,
      };
    }
    const updatedPost = await postModel.findByIdAndUpdate(postId, post);
    if (updatedPost)
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Cập nhật bài viết thành công',
      });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const likePost = async (req, res) => {
  const user = req.decoded;
  const { channelId, postId } = req.params;
  try {
    const alreadyLikePost = await postModel.findOne({
      _id: postId,
      channel: channelId,
    });
    if (!alreadyLikePost)
      return res.status(404).json({
        error: true,
        success: false,
        message: `Không tìm thấy bài viết ${postId}!`,
      });

    if (alreadyLikePost.liked.includes(user._id)) {
      const updatedPost = await postModel.findByIdAndUpdate(
        postId,
        {
          $pull: {
            liked: user._id,
          },
        },
        { new: true }
      );
      if (updatedPost)
        return res.status(200).json({
          error: false,
          success: true,
          message: 'Hủy thích bài viết thành công!',
        });
    }
    if (alreadyLikePost.user !== user._id) {
      await notificationModel.create({
        user: alreadyLikePost.user,
        seeder: user._id,
        notification: `${user.username} just liked your post!`,
        url: `channels/${alreadyLikePost.channel}/posts/${alreadyLikePost._id}`,
      });
    }
    const updatedPost = await postModel.findByIdAndUpdate(
      postId,
      {
        $push: {
          liked: user._id,
        },
      },
      { new: true }
    );
    if (updatedPost)
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Thích bài viết thành công!',
      });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const bookMarkPost = async (req, res) => {
  const user = req.decoded;
  const { channelId, postId } = req.params;
  try {
    const alreadyBookMarkPost = await postModel.findOne({
      _id: postId,
      channel: channelId,
    });
    if (!alreadyBookMarkPost)
      return res.status(404).json({
        error: true,
        success: false,
        message: `Không tìm thấy bài viết ${postId}!`,
      });

    if (alreadyBookMarkPost.book_marked.includes(user._id)) {
      const updatedPost = await postModel.findByIdAndUpdate(
        postId,
        {
          $pull: {
            book_marked: user._id,
          },
        },
        { new: true }
      );
      if (updatedPost)
        return res.status(200).json({
          error: false,
          success: true,
          message: 'Hủy lưu bài viết thành công!',
        });
    }
    if (alreadyBookMarkPost.user !== user._id) {
      await notificationModel.create({
        user: alreadyBookMarkPost.user,
        seeder: user._id,
        notification: `${user.username} just saved your post!`,
        url: null,
      });
    }
    const updatedPost = await postModel.findByIdAndUpdate(
      postId,
      {
        $push: {
          book_marked: user._id,
        },
      },
      { new: true }
    );
    if (updatedPost)
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Lưu bài viết thành công!',
      });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const getBookMark = async (req, res) => {
  const user = req.decoded;
  const { page } = req.query;
  const curPage = page ? Number(page) : 1;
  try {
    const totalPosts = await postModel.countDocuments({
      book_marked: user._id,
    });
    const posts = await postModel
      .find({ book_marked: user._id })
      .populate('user', '_id email username avatar')
      .populate('channel', '_id name')
      .populate('book_marked', '_id email username avatar')
      .skip((curPage - 1) * 10)
      .limit(10);
    return res.status(200).json({
      error: false,
      success: true,
      posts: posts,
      totalPage: Math.ceil(totalPosts / 10),
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const postCommentPost = async (req, res) => {
  const user = req.decoded;
  const { postId, channelId } = req.params;
  const { content } = req.body;
  try {
    if (content === '')
      return res.status(400).json({
        error: true,
        success: false,
        message: 'Không thể đăng bình luận trống!',
      });
    const updatedPost = await postModel.findOneAndUpdate(
      { _id: postId, channel: channelId },
      {
        $push: {
          comments: {
            user: user._id,
            content: content,
            created_at: Date.now(),
          },
        },
      },
      { new: true }
    );
    if (updatedPost) {
      if (updatedPost?.user !== user._id) {
        await notificationModel.create({
          user: updatedPost.user,
          seeder: user._id,
          notification: `${user.username} just commented your post!`,
          url: `channels/${updatedPost.channel}/posts/${updatedPost._id}`,
        });
      }
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Đăng bình luận thành công',
      });
    }
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const deleteCommentPost = async (req, res) => {
  const user = req.decoded;
  const { channelId, postId } = req.params;
  const { commentId } = req.body;
  try {
    const updatedPost = await postModel.findOneAndUpdate(
      { _id: postId, channel: channelId },
      {
        $pull: {
          comments: {
            _id: commentId,
            user: user._id,
          },
        },
      },
      { new: true }
    );
    if (updatedPost)
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Xoá bình luận thành công!',
      });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const deletePost = async (req, res) => {
  const user = req.decoded;
  const { channelId, postId } = req.params;
  try {
    const correctUser = await postModel.findOne({ user: user._id });
    if (!correctUser)
      return res.status(403).json({
        error: true,
        success: false,
        message: 'Bạn không thể xóa bài viết của người khác',
      });
    const deletedPost = await postModel.findOneAndDelete({
      channel: channelId,
      _id: postId,
    });
    if (deletedPost) {
      await deleteFile(deletedPost?.images.url);
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Xóa bài viết thành công!',
      });
    }
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const deletePostByAdmin = async (req, res) => {
  const user = req.decoded;
  const { channelId, postId } = req.params;
  try {
    if (user?.role?.value !== 1)
      return res
        .status(403)
        .json({ error: true, success: false, message: 'Bạn không đủ quyền!' });
    const deletedPost = await postModel.findOneAndDelete({
      channel: channelId,
      _id: postId,
    });
    if (deletedPost) {
      await deleteFile(deletedPost?.images.url);
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Xóa bài viết thành công!',
      });
    }
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
