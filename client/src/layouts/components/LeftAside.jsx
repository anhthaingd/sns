import React, { useCallback, useContext } from 'react';
import { FetchDataContext } from '../../context/FetchDataProvider';
import { icons } from '../../assets/icons';
import { useNavigate } from 'react-router-dom';
import { scrollElement } from '../../services/utils/scrollElement';
import { useGetShortcutsQuery } from '../../services/redux/query/usersQuery';

function LeftAside() {
  const { user, updateShortcut } = useContext(FetchDataContext);
  const navigate = useNavigate();
  const { data: shortcutsData, isSuccess: isSuccessShortcuts } =
    useGetShortcutsQuery();
  const handleRedirect = useCallback(
    (link) => {
      scrollElement();
      navigate(link);
    },
    [navigate]
  );
  const handleRedirectShortcut = useCallback(
    (s) => {
      updateShortcut(s?.channel?._id);
      navigate(`/channels/${s?.channel._id}`);
    },
    [updateShortcut, navigate]
  );
  return (
    <section className='fixed top-0 left-0 mt-[72px] pb-8 w-[350px] h-[95vh] px-4 font-medium hidden lg:flex flex-col gap-8 overflow-y-auto'>
      <div className='pb-6 border-b border-neutral-300'>
        <button
          className='p-2 w-full flex items-center gap-4 hover:bg-neutral-100 dark:hover:bg-neutral-600 rounded'
          onClick={() => handleRedirect(`/profile/${user?._id}`)}
        >
          <img
            className='size-[40px] rounded-full object-cover'
            src={`${import.meta.env.VITE_BACKEND_URL}/${user?.avatar?.url}`}
            alt={user?.username}
          />
          <p className='font-bold'>{user?.username}</p>
        </button>
        <button
          className='p-2 w-full h-[56px] flex items-center gap-4 hover:bg-neutral-100 dark:hover:bg-neutral-600 rounded'
          onClick={() => handleRedirect(`/search`)}
        >
          <span dangerouslySetInnerHTML={{ __html: icons.search_icon }}></span>
          <p>Search</p>
        </button>
        <button
          className='p-2 w-full h-[56px] flex items-center gap-4 hover:bg-neutral-100 dark:hover:bg-neutral-600 rounded'
          onClick={() => handleRedirect(`/profile/${user?._id}`)}
        >
          <span dangerouslySetInnerHTML={{ __html: icons.user_icon }}></span>
          <p>Profile</p>
        </button>
        <button
          className='p-2 w-full h-[56px] flex items-center gap-4 hover:bg-neutral-100 dark:hover:bg-neutral-600 rounded'
          onClick={() => handleRedirect(`/resume`)}
        >
          <span dangerouslySetInnerHTML={{ __html: icons.resume_icon }}></span>
          <p>Resume</p>
        </button>
        <button
          className='p-2 w-full h-[56px] flex items-center gap-4 hover:bg-neutral-100 dark:hover:bg-neutral-600 rounded'
          onClick={() => handleRedirect(`/recruitment`)}
        >
          <span
            dangerouslySetInnerHTML={{ __html: icons.recruitment_icon }}
          ></span>
          <p>Recruitment</p>
        </button>
        <button
          className='p-2 w-full h-[56px] flex items-center gap-4 hover:bg-neutral-100 dark:hover:bg-neutral-600 rounded'
          onClick={() => handleRedirect('/channels')}
        >
          <span dangerouslySetInnerHTML={{ __html: icons.channel_icon }}></span>
          <p>Channels</p>
        </button>
        <button
          className='p-2 w-full h-[56px] flex items-center gap-4 hover:bg-neutral-100 dark:hover:bg-neutral-600 rounded'
          onClick={() => handleRedirect('/bookmarks')}
        >
          <span
            dangerouslySetInnerHTML={{ __html: icons.book_mark_icon }}
          ></span>
          <p>Bookmark</p>
        </button>
        <button
          className='p-2 w-full h-[56px] flex items-center gap-4 hover:bg-neutral-100 dark:hover:bg-neutral-600 rounded'
          onClick={() =>
            handleRedirect(
              `/${
                user?.role?.value === 1 ? 'admin/settings' : 'users/settings'
              }`
            )
          }
        >
          <span
            dangerouslySetInnerHTML={{ __html: icons.settings_icon }}
          ></span>
          <p>Settings</p>
        </button>
        {user?.role?.value === 1 && (
          <button
            className='p-2 w-full h-[56px] flex items-center gap-4 hover:bg-neutral-100 dark:hover:bg-neutral-600 rounded'
            onClick={() => handleRedirect(`/admin/management`)}
          >
            <span
              dangerouslySetInnerHTML={{ __html: icons.management_icon }}
            ></span>
            <p>Management</p>
          </button>
        )}
      </div>
      <div className='flex flex-col gap-4'>
        <p>Your channel's shortcuts</p>
        <div>
          {isSuccessShortcuts &&
            shortcutsData?.shortcuts?.map((s) => {
              return (
                <article
                  key={s._id}
                  className='flex items-center gap-4 hover:bg-neutral-100 dark:hover:bg-neutral-700 p-2 rounded transition-colors cursor-pointer'
                  onClick={() => handleRedirectShortcut(s)}
                >
                  <div className='size-[42px] rounded-full overflow-hidden'>
                    <img
                      className='w-full h-full object-cover'
                      src={`${import.meta.env.VITE_BACKEND_URL}/${
                        s?.channel?.background?.url
                      }`}
                      alt={s?.channel?.background?.name}
                    />
                  </div>
                  <p>{s?.channel?.name}</p>
                </article>
              );
            })}
        </div>
      </div>
    </section>
  );
}

export default LeftAside;
