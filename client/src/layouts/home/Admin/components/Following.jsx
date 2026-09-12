/**
 * Trang quản trị dùng chung đúng thành phần với trang cài đặt người dùng.
 *
 * Trước đây đây là một BẢN SAO từng byte một của
 * `UserSettings/components/Following.jsx`. Hai file giống hệt nhau nghĩa là mọi sửa
 * đổi phải làm hai lần, và trên thực tế chỉ được làm một — nên hai trang dần
 * lệch nhau mà không ai thấy. Giữ lại đường dẫn cũ để router và các nơi import
 * không phải đổi.
 */
export { default } from '../../UserSettings/components/Following';
