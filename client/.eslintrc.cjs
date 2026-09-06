module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  settings: { react: { version: '18.2' } },
  plugins: ['react-refresh', 'i18next'],
  rules: {
    'react/jsx-no-target-blank': 'off',

    // Dự án không dùng PropTypes (cũng không dùng TypeScript), nên rule này
    // chỉ sinh ra 183 lỗi ở mọi component nhận prop — toàn bộ là nhiễu, và
    // chính đống nhiễu đó là lý do không ai chạy lint suốt thời gian qua.
    // Muốn kiểm kiểu prop thật sự thì việc cần làm là chuyển sang TypeScript,
    // không phải rải PropTypes.
    'react/prop-types': 'off',

    // Cảnh báo về Fast Refresh của Vite, không liên quan tới tính đúng đắn.
    // router.jsx cố ý export cả router lẫn component nên luôn vi phạm.
    'react-refresh/only-export-components': 'off',

    // Giữ ở mức cảnh báo: sửa mảng phụ thuộc có thể đổi hành vi runtime, nên
    // phải sửa từng chỗ có kiểm chứng chứ không sửa hàng loạt. CI chốt số
    // lượng cảnh báo hiện tại để con số này chỉ được giảm đi.
    'react-hooks/exhaustive-deps': 'warn',

    // Chặn chuỗi hiển thị viết thẳng trong JSX quay lại sau khi đã làm i18n.
    // Không có rule này, 248 chuỗi vừa dịch xong sẽ có chuỗi thứ 249 lọt vào ở
    // PR sau mà không ai thấy — đây là cách i18n chết dần ở mọi dự án.
    //
    // Để ở mức 'warn' + ngưỡng `--max-warnings` trong package.json: CI chốt số
    // cảnh báo hiện tại nên con số chỉ được phép giảm.
    'i18next/no-literal-string': [
      'warn',
      {
        mode: 'jsx-text-only',
        'should-validate-template': true,
        // Thuộc tính mang chữ cho người đọc -> phải dịch.
        // Những thuộc tính còn lại (className, id, type, role...) là giá trị
        // kỹ thuật, dịch chúng sẽ làm hỏng giao diện.
        words: { exclude: ['^[^a-zA-ZÀ-ỹ぀-鿿]+$'] },
      },
    ],
  },
  overrides: [
    {
      // File cấu hình i18n chứa TÊN GỐC của từng ngôn ngữ ("Tiếng Việt",
      // "日本語"). Đây là thứ duy nhất KHÔNG được dịch: người chỉ đọc được
      // tiếng Việt phải nhận ra dòng "Tiếng Việt" khi giao diện đang là tiếng
      // Nhật, nếu không họ không có cách nào tìm về ngôn ngữ của mình.
      files: ['src/i18n/**'],
      rules: { 'i18next/no-literal-string': 'off' },
    },
  ],
};
