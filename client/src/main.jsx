import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { router } from './services/router/router.jsx';
import './index.css';
// Nạp i18n TRƯỚC khi render: `useTranslation` ở bất kỳ component nào cũng cần
// instance đã init sẵn, kể cả ErrorScreen nằm ngoài cây <App />.
import './i18n/config.js';
import { ModalProvider } from './context/ModalProvider.jsx';
import { Provider } from 'react-redux';
import { store } from './services/redux/store.js';
import { FetchDataProvider } from './context/FetchDataProvider.jsx';
import { SocketProvider } from './context/SocketProvider.jsx';
import { installGlobalErrorHandlers } from './services/logger.js';

// Bắt lỗi nằm ngoài cây React (handler DOM, promise bị bỏ rơi) — ErrorBoundary
// của React không nhìn thấy những lỗi đó.
installGlobalErrorHandlers();
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Provider store={store}>
      <FetchDataProvider>
        <ModalProvider>
          <SocketProvider>
            <RouterProvider router={router} />
          </SocketProvider>
        </ModalProvider>
      </FetchDataProvider>
    </Provider>
  </React.StrictMode>
);
