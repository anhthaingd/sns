import { createBrowserRouter } from 'react-router-dom';
import App from '../../App';
import { lazy } from 'react';
const ProtectedRoute = lazy(() => import('../../auth/ProtectedRoute'));
const HomeLayout = lazy(() => import('../../layouts/home/Home/HomeLayout'));
const ResumeLayout = lazy(() =>
  import('../../layouts/home/Resume/ResumeLayout')
);
const RecruitmentLayout = lazy(() =>
  import('../../layouts/home/Recruitment/RecruitmentLayout')
);
const SearchLayout = lazy(() =>
  import('../../layouts/home/Search/SearchLayout')
);
const ProfileLayout = lazy(() =>
  import('../../layouts/home/Profile/ProfileLayout')
);
const ChannelListLayout = lazy(() =>
  import('../../layouts/home/Channels/ChannelsList/ChannelListLayout')
);
const ChannelDetailsLayout = lazy(() =>
  import('../../layouts/home/Channels/ChanelDetails/ChannelDetailsLayout')
);
const PostDetailsLayout = lazy(() =>
  import(
    '../../layouts/home/Channels/ChanelDetails/PostDetails/PostDetailsLayout'
  )
);
const BookMarkLayout = lazy(() =>
  import('../../layouts/home/BookMark/BookMarkLayout')
);
const AdminSettingsLayout = lazy(() =>
  import('../../layouts/home/Admin/AdminSettingsLayout')
);
const AdminManagementLayout = lazy(() =>
  import('../../layouts/home/Admin/AdminManagementLayout')
);
const UserSettingsLayout = lazy(() =>
  import('../../layouts/home/UserSettings/UserSettingsLayout')
);
const LoginLayout = lazy(() => import('../../layouts/login/LoginLayout'));
const RegisterLayout = lazy(() =>
  import('../../layouts/register/RegisterLayout')
);
const NotFoundLayout = lazy(() =>
  import('../../layouts/notfound/NotFoundLayout')
);
const routes = [
  {
    path: '/',
    element: <App />,
    children: [
      {
        index: true,
        element: (
          <ProtectedRoute>
            <HomeLayout />
          </ProtectedRoute>
        ),
      },
      {
        path: 'resume',
        element: (
          <ProtectedRoute>
            <ResumeLayout />
          </ProtectedRoute>
        ),
      },
      {
        path: 'recruitment',
        element: (
          <ProtectedRoute>
            <RecruitmentLayout />
          </ProtectedRoute>
        ),
      },
      {
        path: 'search',
        element: (
          <ProtectedRoute>
            <SearchLayout />
          </ProtectedRoute>
        ),
      },
      {
        path: 'profile/:id',
        element: (
          <ProtectedRoute>
            <ProfileLayout />
          </ProtectedRoute>
        ),
      },
      {
        path: 'channels',
        children: [
          {
            index: true,
            element: (
              <ProtectedRoute>
                <ChannelListLayout />
              </ProtectedRoute>
            ),
          },
          {
            path: ':id',
            children: [
              {
                index: true,
                element: (
                  <ProtectedRoute>
                    <ChannelDetailsLayout />
                  </ProtectedRoute>
                ),
              },
              {
                path: 'posts/:id',
                element: (
                  <ProtectedRoute>
                    <PostDetailsLayout />
                  </ProtectedRoute>
                ),
              },
            ],
          },
        ],
      },
      {
        path: 'bookmarks',
        element: (
          <ProtectedRoute>
            <BookMarkLayout />
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/management',
        element: (
          <ProtectedRoute>
            <AdminManagementLayout />
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/settings',
        element: (
          <ProtectedRoute>
            <AdminSettingsLayout />
          </ProtectedRoute>
        ),
      },
      {
        path: 'users/settings',
        element: (
          <ProtectedRoute>
            <UserSettingsLayout />
          </ProtectedRoute>
        ),
      },
      {
        path: 'login',
        element: <LoginLayout />,
      },
      {
        path: 'register',
        element: <RegisterLayout />,
      },
      {
        path: '*',
        element: <NotFoundLayout />,
      },
    ],
  },
];

export const router = createBrowserRouter(routes, {
  basename: '/',
  future: {
    v7_normalizeFormMethod: true,
  },
});
