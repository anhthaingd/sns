import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { router } from './services/router/router.jsx';
import './index.css';
import { ModalProvider } from './context/ModalProvider.jsx';
import { Provider } from 'react-redux';
import { store } from './services/redux/store.js';
import { FetchDataProvider } from './context/FetchDataProvider.jsx';
import { SocketProvider } from './context/SocketProvider.jsx';
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
