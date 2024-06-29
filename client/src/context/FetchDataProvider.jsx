import React, { createContext, useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  useGetChannelsByUserQuery,
  useGetNewestMessageQuery,
  useGetUserQuery,
  useUpdateShortcutMutation,
} from '../services/redux/query/usersQuery';
import {
  getToken,
  getUser,
  setUser,
  setWebInfo,
} from '../services/redux/slice/userSlice';
import { useGetWebQuery } from '../services/redux/query/webQuery';
export const FetchDataContext = createContext();
export const FetchDataProvider = ({ children }) => {
  const dispatch = useDispatch();
  const [errorData, setErrorData] = useState(false);
  const user = useSelector(getUser);
  const token = useSelector(getToken);
  const [newestMessages, setNewestMessage] = useState({
    unread: 0,
    messages: [],
  });
  const [followers, setFollowers] = useState([]);
  const [following, setFollowing] = useState([]);
  const [channels, setChannels] = useState([]);
  const {
    data: userData,
    isLoading: isLoadingUser,
    isSuccess: isSuccessUser,
    isError: isErrorUser,
    refetch: refetchUser,
  } = useGetUserQuery(null, { skip: !token });
  const {
    data: messagesData,
    isSuccess: isSuccessMessages,
    refetch: refetchMessages,
  } = useGetNewestMessageQuery(null, { skip: !token || !user });
  const { data: channelsData, isSuccess: isSuccessChannels } =
    useGetChannelsByUserQuery(null, { skip: !user });
  const { data: webData, isSuccess: isSuccessWeb } = useGetWebQuery();
  const [updateShortcut] = useUpdateShortcutMutation();
  useEffect(() => {
    if (isSuccessUser && userData) {
      dispatch(setUser(userData?.user));
      setFollowers([...userData?.followers]);
      setFollowing([...userData?.following]);
      setErrorData(false);
    }
    if (isErrorUser) {
      setErrorData(true);
    }
  }, [isSuccessUser, userData, dispatch, isErrorUser]);
  useEffect(() => {
    if (isSuccessMessages && messagesData) {
      setNewestMessage({
        unread: messagesData?.unread,
        messages: messagesData?.messages,
      });
    }
  }, [isSuccessMessages, messagesData]);
  useEffect(() => {
    if (token) {
      refetchUser();
    }
  }, [token]);
  useEffect(() => {
    if (isSuccessWeb && webData) {
      dispatch(setWebInfo(webData?.website));
    }
  }, [isSuccessWeb, webData]);
  useEffect(() => {
    if (isSuccessChannels && channelsData) {
      setChannels([...channelsData?.channels]);
    }
  }, [isSuccessChannels && channelsData]);
  return (
    <FetchDataContext.Provider
      value={{
        user,
        followers,
        following,
        channels,
        newestMessages,
        refetchMessages,
        isLoadingUser,
        errorData,
        updateShortcut,
      }}
    >
      {children}
    </FetchDataContext.Provider>
  );
};
