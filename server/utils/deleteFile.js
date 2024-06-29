import fs from 'fs';

export const deleteFile = async (imagePath) => {
  fs.access(imagePath, fs.constants.F_OK, (err) => {
    if (err) {
      console.error('Tệp tin không tồn tại hoặc không thể truy cập.');
      return;
    }

    // Xóa tệp tin ảnh
    fs.unlink(imagePath, (err) => {
      if (err) {
        console.error('Lỗi khi xóa tệp tin:', err);
        return;
      }
      console.log('Tệp tin ảnh đã được xóa thành công.');
    });
  });
};
