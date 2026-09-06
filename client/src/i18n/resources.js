/**
 * Toàn bộ bản dịch, gom sẵn thành một module.
 *
 * `virtual:i18n-resources` do `vite-plugin-i18n-resources.js` sinh ra: nó đọc
 * `locales/<ngôn ngữ>/<namespace>.json` ở phía Node rồi trả về một object duy
 * nhất. Lý do không import trực tiếp từng file nằm trong phần chú thích đầu
 * plugin — tóm tắt: 36 file JSON = 36 request ở chế độ dev.
 *
 * Thêm một namespace hoặc một ngôn ngữ chỉ cần thêm file, không phải sửa ở đây.
 */
import resources from 'virtual:i18n-resources';

export default resources;
