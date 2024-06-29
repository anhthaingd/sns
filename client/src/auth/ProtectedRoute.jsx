import React, { useContext } from 'react';
import { FetchDataContext } from '../context/FetchDataProvider';
import { Navigate } from 'react-router-dom';
import { getAccessToken } from '../services/utils/token';
function ProtectedRoute({ children }) {
  const { errorData } = useContext(FetchDataContext);
  const token = getAccessToken();
  if (!token || errorData) return <Navigate to='/login' replace />;
  return children;
}

export default ProtectedRoute;
