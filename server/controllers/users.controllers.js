import { userModel } from '../models/user.model.js';
import bcryptjs from 'bcryptjs';
import { signToken } from '../utils/signToken.js';
import { deleteFile } from '../utils/deleteFile.js';
import { followerModel } from '../models/followers.model.js';
import { followingModel } from '../models/following.model.js';
import { blackList } from '../utils/blackList.js';
import { roleModel } from '../models/roles.model.js';
import { postModel } from '../models/post.model.js';
import { channelModel } from '../models/channels.model.js';
import unidecode from 'unidecode';
import { resumeModel } from '../models/resume.model.js';
export const getUserByToken = async (req, res) => {
  const user = req.decoded;
  try {
    const [existedUser, followers, following] = await Promise.all([
      userModel.findOne({ email: user.email }).populate('role'),
      followerModel
        .findOne({
          user: user._id,
        })
        .populate('followers', '_id email username avatar'),
      followingModel
        .findOne({
          user: user._id,
        })
        .populate('following', '_id email username avatar'),
    ]);
    if (existedUser)
      return res.status(200).json({
        error: false,
        success: true,
        user: existedUser,
        followers: followers?.followers ? followers?.followers : [],
        following: following?.following ? following?.following : [],
      });
    return res.status(404).json({
      error: true,
      success: false,
      message: 'Không tìm thấy người dùng!',
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const getFollowers = async (req, res) => {
  const user = req.decoded;
  const { page } = req.query;
  const curPage = page ? Number(page) : 1;
  try {
    const totalFollowers = await followerModel.countDocuments({
      user: user._id,
    });
    const followers = await followerModel
      .findOne({ user: user._id })
      .populate('followers', '_id email username avatar')
      .skip((curPage - 1) * 20)
      .limit(20);
    return res.status(200).json({
      error: false,
      success: true,
      ...followers._doc,
      totalPage: Math.ceil(totalFollowers / 20),
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const getFollowing = async (req, res) => {
  const user = req.decoded;
  const { page } = req.query;
  const curPage = page ? Number(page) : 1;
  try {
    const totalFollowing = await followingModel.countDocuments({
      user: user._id,
    });
    const following = await followingModel
      .findOne({ user: user._id })
      .populate('following', '_id email username avatar')
      .skip((curPage - 1) * 20)
      .limit(20);
    return res.status(200).json({
      error: false,
      success: true,
      ...following._doc,
      totalPage: Math.ceil(totalFollowing / 20),
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const registerUser = async (req, res) => {
  const { email, password, username, address, intro } = req.body;
  try {
    if (!email || !password)
      return res.status(400).json({
        error: true,
        success: false,
        message: 'Yêu cầu cần có email và password!',
      });
    const duplicatedUser = await userModel.findOne({ email: email });
    if (duplicatedUser)
      return res.status(409).json({
        error: false,
        success: true,
        message: 'Địa chỉ email đã tồn tại!',
      });
    const userRole = await roleModel.findOne({ value: 0 });
    const hasPwd = bcryptjs.hashSync(password, 10);
    const createdUser = await userModel.create({
      email: email,
      password: hasPwd,
      username: username,
      address: address,
      intro: intro,
      role: userRole._id,
    });
    await Promise.all([
      followerModel.create({ user: createdUser._doc._id }),
      followingModel.create({ user: createdUser._doc._id }),
    ]);
    if (createdUser)
      return res.status(201).json({
        error: false,
        success: true,
        message: 'Tạo tài khoản thành công!',
      });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const loginUser = async (req, res) => {
  const { email, password } = req.body;

  try {
    const existedUser = await userModel
      .findOne({ email: email })
      .populate('role');
    if (!existedUser)
      return res.status(404).json({
        error: true,
        success: false,
        message: 'Tài khoản chưa được đăng ký!',
      });
    const match = bcryptjs.compareSync(password, existedUser.password);
    console.log(match);
    if (!match)
      return res
        .status(403)
        .json({ error: true, success: false, message: 'Sai mật khẩu!' });
    const token = await signToken({ ...existedUser._doc });
    return res
      .status(200)
      .json({ error: false, success: true, accessToken: token });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const logoutUser = async (req, res) => {
  const token = req.headers['authorization'];
  const getToken = token?.split(' ')[1];
  blackList.add(getToken);
  return res.status(200).json({
    error: false,
    success: true,
    message: 'Đăng xuất tài khoản thành công!',
  });
};
export const getUserDetails = async (req, res) => {
  const { id } = req.params;
  try {
    const [existedUser, followers, following, posts, channels] =
      await Promise.all([
        userModel
          .findOne(
            { _id: id },
            {
              _id: 1,
              avatar: 1,
              cover_bg: 1,
              username: 1,
              email: 1,
              role: 1,
              intro: 1,
              address: 1,
            }
          )
          .populate('role'),
        followerModel
          .findOne({
            user: id,
          })
          .populate('followers', '_id email username avatar'),
        followingModel
          .findOne({
            user: id,
          })
          .populate('following', '_id email username avatar'),
        postModel.countDocuments({ user: id }),
        channelModel.countDocuments({ members: id }),
      ]);
    if (existedUser)
      return res.status(200).json({
        error: false,
        success: true,
        user: existedUser,
        followers: followers?.followers ? followers?.followers : [],
        following: following?.following ? following?.following : [],
        posts: posts,
        channels: channels,
      });
    return res.status(404).json({
      error: true,
      success: false,
      message: 'Không tìm thấy người dùng!',
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const updateUser = async (req, res) => {
  const { id } = req.params;
  const {
    username,
    oldPassword,
    newPassword,
    address,
    intro,
    oldAvatar,
    oldCoverBg,
    update_images,
  } = req.body;
  const files = req.files;
  const parseOldAvatar = oldAvatar ? JSON.parse(oldAvatar) : null;
  const parseOldCoverBg = oldCoverBg ? JSON.parse(oldCoverBg) : null;
  try {
    const updatedUser = {
      username: username,
      address: address,
      intro: intro,
      updated_at: Date.now(),
    };
    if (newPassword !== oldPassword) {
      const hasPwd = bcryptjs.hashSync(newPassword, 10);
      updatedUser.password = hasPwd;
    }
    if (files.images && files?.images?.length > 0) {
      if (update_images === 'both') {
        updatedUser.avatar = {
          name: files?.images[0]?.filename,
          url: files?.images[0]?.path,
        };
        if (parseOldAvatar?.name !== 'avatar_trang.jpg') {
          await deleteFile(parseOldAvatar?.url);
        }
        updatedUser.cover_bg = {
          name: files?.images[1]?.filename,
          url: files?.images[1]?.path,
        };
      }
      if (update_images === 'avatar') {
        if (parseOldAvatar?.name !== 'avatar_trang.jpg') {
          await deleteFile(parseOldAvatar?.url);
        }
        updatedUser.avatar = {
          name: files?.images[0]?.filename,
          url: files?.images[0]?.path,
        };
      }
      if (update_images === 'cover_bg') {
        updatedUser.cover_bg = {
          name: files?.images[0]?.filename,
          url: files?.images[0]?.path,
        };
        await deleteFile(parseOldCoverBg?.url || '');
      }
    }
    const updated = await userModel.findByIdAndUpdate(id, { ...updatedUser });
    if (updated)
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Cập nhật người dùng thành công!',
      });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const followingUser = async (req, res) => {
  const user = req.decoded;
  const { id } = req.params;

  try {
    if (user._id === id) {
      return res.status(409).json({
        error: true,
        success: false,
        message: 'Bạn không thể tự follow bản thân!',
      });
    }

    const alreadyFollowed = await followingModel.findOne({ user: user._id });

    if (alreadyFollowed && alreadyFollowed.following.includes(id)) {
      const [pullFollowing, pullFollowers] = await Promise.all([
        followingModel.findOneAndUpdate(
          { user: user._id },
          { $pull: { following: id } },
          { new: true }
        ),
        followerModel.findOneAndUpdate(
          { user: id },
          { $pull: { followers: user._id } },
          { new: true }
        ),
      ]);

      if (pullFollowing && pullFollowers) {
        return res.status(200).json({
          error: false,
          success: true,
          message: 'Hủy follow tài khoản thành công!',
        });
      }
    } else {
      const [pushFollowing, pushFollowers] = await Promise.all([
        followingModel.findOneAndUpdate(
          { user: user._id },
          { $push: { following: id } },
          { new: true }
        ),
        followerModel.findOneAndUpdate(
          { user: id },
          { $push: { followers: user._id } },
          { new: true }
        ),
      ]);

      if (pushFollowing && pushFollowers) {
        return res.status(200).json({
          error: false,
          success: true,
          message: 'Follow tài khoản thành công!',
        });
      }
    }
  } catch (error) {
    return res.status(500).json({
      error: true,
      success: false,
      message: error.message,
    });
  }
};
export const removeFollowing = async (req, res) => {
  const user = req.decoded;
  const { id } = req.params;
  try {
    const [pullFollowing, pullFollowers] = await Promise.all([
      followingModel.findOneAndUpdate(
        { user: user._id },
        { $pull: { following: id } },
        { new: true }
      ),
      followerModel.findOneAndUpdate(
        { user: id },
        { $pull: { followers: user._id } },
        { new: true }
      ),
    ]);

    if (pullFollowing && pullFollowers) {
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Hủy theo dõi người dùng thành công!',
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
export const removeFollowers = async (req, res) => {
  const user = req.decoded;
  const { id } = req.params;
  try {
    const [pullFollowing, pullFollowers] = await Promise.all([
      followingModel.findOneAndUpdate(
        { user: id },
        { $pull: { following: user._id } },
        { new: true }
      ),
      followerModel.findOneAndUpdate(
        { user: user._id },
        { $pull: { followers: id } },
        { new: true }
      ),
    ]);

    if (pullFollowing && pullFollowers) {
      return res.status(200).json({
        error: false,
        success: true,
        message: 'Gỡ thành công người dùng ra khỏi danh sách theo dõi!',
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

export const searchUsers = async (req, res) => {
  const user = req.decoded;
  const { search, page } = req.query;
  const curPage = page ? Number(page) : 1;
  try {
    if (!search || !page)
      return res.status(200).json({
        error: true,
        success: false,
        users: [],
        totalPage: 1,
        totalUsers: 0,
      });
    const query = {
      _id: { $ne: user._id },
      $or: [
        { username: { $regex: search, $options: 'i' } },
        { email: { $regex: search, $options: 'i' } },
      ],
    };
    const totalUsers = await userModel.countDocuments(query);
    const users = await userModel
      .find(query)
      .skip((curPage - 1) * 10)
      .limit(10);
    return res.status(200).json({
      error: false,
      success: true,
      users: users?.map((u) => {
        return {
          _id: u?._id,
          avatar: u?.avatar,
          username: u?.username,
          email: u?.email,
        };
      }),
      totalPage: Math.ceil(totalUsers / 10),
      totalUsers: totalUsers,
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};

export const getUsersByAdmin = async (req, res) => {
  const user = req.decoded;
  const { page, search } = req.query;
  const curPage = page ? Number(page) : 1;
  let query = {};
  try {
    if (user?.role?.value !== 1)
      return res
        .status(403)
        .json({ error: true, success: false, message: 'Bạn không đủ quyền!' });
    query.role = {
      $ne: user?.role?._id,
    };
    if (
      search &&
      search !== 'null' &&
      search !== null &&
      search.trim() !== ''
    ) {
      const unaccentedQueryString = unidecode(search);
      const regex = new RegExp(unaccentedQueryString, 'i');
      query.username = regex;
    }
    const totalUsers = await userModel.countDocuments(query);
    const users = await userModel
      .find(query, {
        _id: 1,
        username: 1,
        email: 1,
        avatar: 1,
        created_at: 1,
        updated_at: 1,
        address: 1,
      })
      .skip((curPage - 1) * 10)
      .limit(10);
    return res.status(200).json({
      error: false,
      success: true,
      users: users,
      totalPage: Math.ceil(totalUsers / 10),
      totalUsers: totalUsers,
      curPage: curPage,
    });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
function filterDifferentElements(arr1, arr2) {
  // Lọc ra các phần tử mà không có trong mảng thứ hai
  let differentElements = arr1.filter(
    (obj1) =>
      !arr2.some((obj2) => obj2.name === obj1.name && obj2.value === obj1.value)
  );

  // Lọc ra các phần tử mà không có trong mảng thứ nhất
  differentElements = differentElements.concat(
    arr2.filter(
      (obj2) =>
        !arr1.some(
          (obj1) => obj1.name === obj2.name && obj1.value === obj2.value
        )
    )
  );

  return differentElements;
}
export const getResume = async (req, res) => {
  const user = req.decoded;
  try {
    const resume = await resumeModel.findOne({ user: user._id });
    return res
      .status(200)
      .json({ error: false, success: true, resume: resume });
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
export const postResume = async (req, res) => {
  const user = req.decoded;
  const {
    name,
    position,
    oldAvatar,
    birthday,
    email,
    address,
    phone,
    github,
    objective,
    educationName,
    educationMajor,
    educationCompletion,
    educationGPA,
    certificatesName,
    oldCertificates,
    editCertificates,
    experiences,
    skills,
    languages,
    projects,
  } = req.body;
  const files = req.files;
  const parseJson = (jsonString) => {
    try {
      let jsonStr = jsonString ? JSON.parse(jsonString) : null;
      return jsonStr;
    } catch (error) {
      console.error('Error parsing JSON:', error);
      return null;
    }
  };
  const parseOldAvatar = parseJson(oldAvatar);
  const parseCertificateName = parseJson(certificatesName) || [];
  const parseOldCertificates = parseJson(oldCertificates) || [];
  const parseEditCertificates = parseJson(editCertificates) || [];
  try {
    const resume = {
      user: user._id,
      name,
      position,
      birthday,
      email,
      address,
      phone,
      github,
      objective,
      educationName,
      educationMajor,
      educationCompletion,
      educationGPA,
      experiences: parseJson(experiences) || [],
      skills: parseJson(skills) || [],
      languages: parseJson(languages) || [],
      projects: parseJson(projects) || [],
    };
    const existedResume = await resumeModel.findOne({ user: user._id });
    if (existedResume) {
      if (parseOldCertificates) {
        const filterCertificates = filterDifferentElements(
          parseOldCertificates,
          parseEditCertificates
        );
        filterCertificates.map(async (file) => {
          return await deleteFile(file.url);
        });
      }
      if (files.avatar) {
        parseOldAvatar?.url && (await deleteFile(parseOldAvatar?.url));
        resume.avatar = {
          name: files.avatar[0].filename,
          url: files.avatar[0].path,
        };
      }
      if (
        files.certificates &&
        files?.certificates?.length > 0 &&
        parseCertificateName
      ) {
        const newCertificates = files?.certificates?.map((file, index) => {
          return {
            name: parseCertificateName[index],
            url: file.path,
          };
        });
        const certificatesUrls = await Promise.all(newCertificates);
        resume.certificates = [...parseEditCertificates, ...certificatesUrls];
      }
      const updatedResume = await resumeModel.findOneAndUpdate(
        { user: user._id },
        resume
      );
      if (updatedResume)
        return res
          .status(200)
          .json({ error: false, success: true, message: 'Lưu CV thành công!' });
    }
    const createdResume = await resumeModel.create(resume);
    if (createdResume) {
      return res
        .status(200)
        .json({ error: false, success: true, message: 'Lưu CV thành công!' });
    }
  } catch (error) {
    return res
      .status(500)
      .json({ error: true, success: false, message: error.message });
  }
};
