import { useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';

const useQueryString = () => {
  const [searchQuery, setSearchQuery] = useSearchParams();
  const createQueryString = useCallback(
    (name, value) => {
      const newQuery = new URLSearchParams(searchQuery.toString());
      if (Array.isArray(name) && Array.isArray(value)) {
        name.forEach((query, index) => {
          newQuery.set(query, value[index]);
        });
      } else {
        if (value) {
          newQuery.set(name, value);
          name !== 'page' && newQuery.set('page', '1');
        }
      }
      setSearchQuery(newQuery.toString());
    },
    [searchQuery]
  );
  const deleteQueryString = useCallback(() => {
    const newQuery = new URLSearchParams();
    newQuery.set('page', 1);
    setSearchQuery(newQuery.toString());
  }, [searchQuery]);
  return [createQueryString, deleteQueryString];
};

export default useQueryString;
