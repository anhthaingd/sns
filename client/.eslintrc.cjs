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
  plugins: ['react-refresh'],
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
  },
};
