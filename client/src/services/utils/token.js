export const getAccessToken = () => {
  return window.localStorage.getItem('social_app_token');
};

export const getLocalStorage = (name) => {
  return window.localStorage.getItem(name);
};
export const setLocalStorage = (name, value) => {
  return window.localStorage.setItem(name, value);
};
export const deleteLocalStorage = (name) => {
  return window.localStorage.removeItem(name);
};
