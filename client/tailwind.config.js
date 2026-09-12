/** @type {import('tailwindcss').Config} */

/**
 * Hệ màu Fuurin — lấy từ bảng màu nhuộm truyền thống Nhật (和色).
 *
 *   ai    藍   chàm    — màu thương hiệu, dùng cho điều hướng và tiêu đề
 *   asagi 浅葱 xanh lam — màu tương tác: liên kết, mục đang chọn, biểu đồ
 *   shu   朱   son đỏ  — chỉ dùng cho cảnh báo và huy hiệu thông báo
 *   washi 和紙 giấy    — nền sáng
 *   sumi  墨   mực     — nền tối
 *
 * Hai lớp màu:
 *   1. Thang màu tĩnh (ai/asagi/shu/...) — giá trị cố định, dùng khi cần đúng
 *      một sắc độ cụ thể.
 *   2. Token ngữ nghĩa (bg/surface/fg/border/brand/...) — đọc từ biến CSS nên
 *      tự đổi theo sáng/tối. ĐÂY là thứ nên dùng trong hầu hết trường hợp, để
 *      không phải viết `dark:` cho từng class một.
 */
const semantic = (name) => `rgb(var(--fu-${name}) / <alpha-value>)`;

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // ---- Thang màu tĩnh -------------------------------------------------
        ai: {
          50: '#EEF2F9',
          100: '#D8E1F0',
          200: '#B3C4E0',
          300: '#8AA3CC',
          400: '#5C7DB3',
          500: '#3D5F98',
          600: '#274A78',
          700: '#1E3A60',
          800: '#172D4A',
          900: '#101F33',
          950: '#0A1523',
        },
        asagi: {
          50: '#E6F5F5',
          100: '#C2E8E8',
          200: '#8FD6D6',
          300: '#54BEBE',
          400: '#21A3A3',
          500: '#0F8C8C',
          600: '#0A7070',
          700: '#075858',
          800: '#064545',
          900: '#043030',
        },
        shu: {
          50: '#FCEDE9',
          100: '#F8D5CC',
          200: '#F0AC9B',
          300: '#E67F66',
          400: '#DC5837',
          500: '#C43C1B',
          600: '#A22F14',
          700: '#7E2410',
          800: '#5E1B0C',
          900: '#401208',
        },
        matcha: {
          100: '#DDEBDF',
          300: '#8FBE9B',
          500: '#3F7D4E',
          600: '#33653F',
          700: '#274E31',
        },
        yamabuki: {
          100: '#FBEFD4',
          300: '#E8C167',
          500: '#C9922B',
          600: '#A47522',
          700: '#7E591A',
        },

        // ---- Token ngữ nghĩa (theo chế độ sáng/tối) --------------------------
        bg: semantic('bg'),
        'bg-alt': semantic('bg-alt'),
        surface: semantic('surface'),
        'surface-2': semantic('surface-2'),
        'surface-3': semantic('surface-3'),
        line: semantic('line'),
        'line-strong': semantic('line-strong'),
        fg: semantic('fg'),
        'fg-muted': semantic('fg-muted'),
        'fg-subtle': semantic('fg-subtle'),
        'fg-inverse': semantic('fg-inverse'),
        brand: semantic('brand'),
        'brand-hover': semantic('brand-hover'),
        'brand-soft': semantic('brand-soft'),
        'brand-text': semantic('brand-text'),
        'brand-on': semantic('brand-on'),
        accent: semantic('accent'),
        'accent-hover': semantic('accent-hover'),
        'accent-soft': semantic('accent-soft'),
        'accent-text': semantic('accent-text'),
        'accent-on': semantic('accent-on'),
        danger: semantic('danger'),
        'danger-soft': semantic('danger-soft'),
        'danger-text': semantic('danger-text'),
        success: semantic('success'),
        'success-soft': semantic('success-soft'),
        'success-text': semantic('success-text'),
        warning: semantic('warning'),
        'warning-soft': semantic('warning-soft'),
        'warning-text': semantic('warning-text'),
      },

      fontFamily: {
        // Zen Kaku Gothic New là font do xưởng chữ Nhật thiết kế: phủ cả kana,
        // kanji lẫn Latin có dấu tiếng Việt, nên tiêu đề ở cả ba ngôn ngữ đều
        // cùng một giọng.
        display: [
          '"Zen Kaku Gothic New"',
          '"Hiragino Kaku Gothic ProN"',
          '"Noto Sans JP"',
          'system-ui',
          'sans-serif',
        ],
        sans: [
          'Inter',
          '"Zen Kaku Gothic New"',
          '"Hiragino Kaku Gothic ProN"',
          '"Noto Sans JP"',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },

      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem', letterSpacing: '0.01em' }],
      },

      borderRadius: {
        card: '0.875rem',
        pill: '999px',
      },

      boxShadow: {
        card: '0 1px 2px rgb(16 31 51 / 0.04), 0 1px 3px rgb(16 31 51 / 0.05)',
        'card-hover':
          '0 2px 4px rgb(16 31 51 / 0.05), 0 8px 20px rgb(16 31 51 / 0.08)',
        pop: '0 4px 12px rgb(16 31 51 / 0.08), 0 16px 40px rgb(16 31 51 / 0.12)',
        modal: '0 8px 24px rgb(16 31 51 / 0.12), 0 32px 72px rgb(16 31 51 / 0.20)',
        // Viền trong, dùng thay border để không cộng thêm 1px vào kích thước.
        edge: 'inset 0 0 0 1px rgb(var(--fu-line) / 1)',
      },

      spacing: {
        header: '3.75rem', // 60px — chiều cao thanh trên cùng
        nav: '15rem', // 240px — cột điều hướng trái
        rail: '19rem', // 304px — cột phụ phải
      },

      maxWidth: {
        feed: '40rem',
        shell: '96rem',
      },

      keyframes: {
        'fu-fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'fu-rise': {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'fu-pop': {
          from: { opacity: '0', transform: 'translateY(-4px) scale(0.98)' },
          to: { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        'fu-shimmer': {
          '100%': { transform: 'translateX(100%)' },
        },
        // Chuông gió đung đưa — chỉ dùng cho logo khi rê chuột.
        'fu-sway': {
          '0%, 100%': { transform: 'rotate(0deg)' },
          '25%': { transform: 'rotate(-7deg)' },
          '75%': { transform: 'rotate(7deg)' },
        },
        'fu-spin-slow': {
          to: { transform: 'rotate(360deg)' },
        },
      },
      animation: {
        'fade-in': 'fu-fade-in 0.18s ease-out',
        rise: 'fu-rise 0.22s cubic-bezier(0.22, 1, 0.36, 1)',
        pop: 'fu-pop 0.15s cubic-bezier(0.22, 1, 0.36, 1)',
        shimmer: 'fu-shimmer 1.6s infinite',
        sway: 'fu-sway 1.2s ease-in-out',
        'spin-slow': 'fu-spin-slow 1.1s linear infinite',
      },

      transitionTimingFunction: {
        out: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
    },
  },
  plugins: [],
};
