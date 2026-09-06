/**
 * Gom toàn bộ file dịch thành MỘT module ảo `virtual:i18n-resources`.
 *
 * Vì sao không dùng `import.meta.glob`
 * ------------------------------------
 * Cách đó chạy đúng, nhưng ở chế độ dev Vite phục vụ mỗi file JSON như một
 * module riêng: 3 ngôn ngữ × 12 namespace = **36 request thêm vào mỗi lần tải
 * trang**. Đo trên chính dự án này, trang đăng nhập đi từ 82 lên 118 request —
 * tức là gần một phần ba số request chỉ để lấy chữ. Mở hai tab cùng lúc trong
 * container CI thì Chromium hết hạn mức tài nguyên mạng và tab chết với lỗi
 * `net::ERR_INSUFFICIENT_RESOURCES`, không kèm bất kỳ lỗi JavaScript nào — rất
 * khó truy ra nguyên nhân.
 *
 * Đọc file ở phía Node rồi trả về một module duy nhất thì còn đúng 1 request,
 * và bản build production cũng nhẹ hơn vì không phải sinh 36 chunk nhỏ.
 *
 * Vẫn giữ được cách tổ chức mỗi namespace một file: đó là thứ khiến file dịch
 * còn đọc được khi số khoá lên tới hàng trăm.
 */
import fs from 'node:fs';
import path from 'node:path';

const VIRTUAL_ID = 'virtual:i18n-resources';
const RESOLVED_ID = '\0' + VIRTUAL_ID;

const readCatalogs = (dir) => {
  const resources = {};
  const files = [];
  for (const lng of fs.readdirSync(dir)) {
    const langDir = path.join(dir, lng);
    if (!fs.statSync(langDir).isDirectory()) continue;
    resources[lng] = {};
    for (const file of fs.readdirSync(langDir)) {
      if (!file.endsWith('.json')) continue;
      const full = path.join(langDir, file);
      resources[lng][file.slice(0, -5)] = JSON.parse(fs.readFileSync(full, 'utf8'));
      files.push(full);
    }
  }
  return { resources, files };
};

export default function i18nResources({ dir }) {
  return {
    name: 'fuurin-i18n-resources',
    resolveId(id) {
      return id === VIRTUAL_ID ? RESOLVED_ID : null;
    },
    load(id) {
      if (id !== RESOLVED_ID) return null;
      const { resources, files } = readCatalogs(dir);
      // Khai báo phụ thuộc để `vite build --watch` biết phải dựng lại.
      for (const file of files) this.addWatchFile(file);
      return `export default ${JSON.stringify(resources)};`;
    },
    configureServer(server) {
      // Sửa file dịch -> nạp lại trang. Không có đoạn này thì phải khởi động
      // lại dev server mỗi lần đổi một câu chữ.
      const onChange = (file) => {
        if (!file.startsWith(dir) || !file.endsWith('.json')) return;
        const mod = server.moduleGraph.getModuleById(RESOLVED_ID);
        if (mod) server.moduleGraph.invalidateModule(mod);
        server.ws.send({ type: 'full-reload' });
      };
      server.watcher.on('change', onChange);
      server.watcher.on('add', onChange);
      server.watcher.on('unlink', onChange);
    },
  };
}
