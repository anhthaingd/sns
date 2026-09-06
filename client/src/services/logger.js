/**
 * Nơi duy nhất để ghi log ở frontend.
 *
 * Vì sao cần: trước đây lỗi phía trình duyệt chỉ nằm trong console của máy
 * người dùng. Một lỗi render làm trắng trang mà không để lại dấu vết nào ở
 * backend, nên khi ai đó báo "web bị lỗi" thì không có gì để tra.
 *
 * Ba nguồn lỗi đều đổ về đây:
 *   1. Lỗi render  -> ErrorScreen (errorElement của router)
 *   2. Lỗi API     -> middleware errorLogger của RTK Query
 *   3. Lỗi ngoài React (window.onerror, promise không ai bắt)
 *
 * Nguyên tắc bất di bất dịch: **logger không bao giờ được ném lỗi**. Một bộ
 * ghi log làm sập ứng dụng thì tệ hơn là không có log. Mọi thứ trong file này
 * đều bọc try/catch và thất bại trong im lặng.
 */

import { endpoint } from '../config/endpoint';

const LOG_PATH = 'client_logs';
const LOG_URL = `${endpoint}${LOG_PATH}`;

// Gửi log là việc phụ; không bao giờ được để nó làm chậm hay treo giao diện.
const SEND_TIMEOUT_MS = 4000;

// Một vòng lặp render hỏng có thể bắn hàng nghìn lỗi giống hệt nhau trong vài
// giây. Hai chốt chặn dưới đây giữ cho backend không bị ngập và người dùng
// không bị tốn băng thông vô ích.
const DEDUPE_WINDOW_MS = 30_000;
const MAX_SENT_PER_SESSION = 50;

const recentlySent = new Map(); // chữ ký -> thời điểm gửi gần nhất
let sentCount = 0;

const isDev = import.meta.env.DEV;

/** Cắt ngắn để không gửi cả một stack dài vô tận lên server. */
const clamp = (value, max) => {
  if (typeof value !== 'string') return undefined;
  return value.length > max ? `${value.slice(0, max)}…` : value;
};

const signatureOf = (level, event, message) => `${level}|${event}|${message}`;

const shouldSend = (level, event, message) => {
  if (sentCount >= MAX_SENT_PER_SESSION) return false;

  const now = Date.now();
  const signature = signatureOf(level, event, message);
  const last = recentlySent.get(signature);
  if (last && now - last < DEDUPE_WINDOW_MS) return false;

  recentlySent.set(signature, now);
  // Dọn các chữ ký đã hết hạn để Map không phình mãi.
  for (const [key, at] of recentlySent) {
    if (now - at >= DEDUPE_WINDOW_MS) recentlySent.delete(key);
  }
  return true;
};

const send = (payload) => {
  // Nếu chính request gửi log lại lỗi thì sẽ sinh ra log mới -> vòng lặp vô
  // tận. `keepalive` để log vẫn đi được cả khi người dùng vừa đóng tab.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), SEND_TIMEOUT_MS);

  fetch(LOG_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    keepalive: true,
    signal: controller.signal,
  })
    .catch(() => {})
    .finally(() => clearTimeout(timer));
};

const write = (level, event, detail = {}) => {
  try {
    const message = clamp(String(detail.message ?? ''), 500) || event;
    const payload = {
      level,
      event: clamp(String(event), 100),
      message,
      url: clamp(window.location?.pathname + window.location?.search, 300),
      stack: clamp(detail.stack, 2000),
    };

    if (isDev) {
      const fn = level === 'error' ? console.error : console.warn;
      fn(`[fuurin:${level}] ${payload.event}`, detail);
    }

    // Chỉ đẩy warn/error về backend. info/debug chỉ để xem lúc phát triển —
    // gửi hết thì log server thành bãi rác và mất luôn tác dụng cảnh báo.
    if ((level === 'error' || level === 'warn') && shouldSend(level, event, message)) {
      sentCount += 1;
      send(payload);
    }
  } catch {
    // Cố tình nuốt: xem chú thích đầu file.
  }
};

export const logger = {
  error: (event, detail) => write('error', event, detail),
  warn: (event, detail) => write('warn', event, detail),
  info: (event, detail) => {
    if (isDev) console.info(`[fuurin:info] ${event}`, detail ?? '');
  },
};

/**
 * Bắt các lỗi nằm NGOÀI cây React: handler DOM, setTimeout, promise bị bỏ rơi.
 * ErrorBoundary của React không thấy được những lỗi này.
 */
export const installGlobalErrorHandlers = () => {
  window.addEventListener('error', (e) => {
    logger.error('window.error', {
      message: e?.message,
      stack: e?.error?.stack || `${e?.filename}:${e?.lineno}:${e?.colno}`,
    });
  });

  window.addEventListener('unhandledrejection', (e) => {
    const reason = e?.reason;
    logger.error('unhandled.rejection', {
      message: reason?.message || String(reason),
      stack: reason?.stack,
    });
  });
};

export default logger;
