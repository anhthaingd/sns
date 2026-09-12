const BASE = import.meta.env.VITE_BACKEND_URL || '';

/**
 * Dựng URL đầy đủ cho file do server trả về.
 *
 * Khắp dự án trước đây viết thẳng `${import.meta.env.VITE_BACKEND_URL}/${x?.url}`.
 * Khi `x` chưa có (đang tải, người dùng chưa đặt ảnh) chuỗi đó thành
 * ".../undefined" — trình duyệt vẫn gọi, nhận 404 và vẽ biểu tượng ảnh vỡ.
 * Ở đây trả về null để nơi gọi biết mà dựng ảnh thay thế.
 *
 * @param {{url?: string}|string|null|undefined} file
 * @returns {string|null}
 */
export function mediaUrl(file) {
  const path = typeof file === 'string' ? file : file?.url;
  if (!path || path === 'undefined' || path === 'null') return null;
  if (/^(https?:)?\/\//.test(path) || path.startsWith('data:')) return path;
  return `${BASE}/${path.replace(/^\/+/, '')}`;
}

export default mediaUrl;
