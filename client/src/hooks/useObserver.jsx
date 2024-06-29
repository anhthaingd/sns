import { useEffect, useRef } from 'react';

function useObserver(hasMore, curPage, setCurPage, isSuccess, data, totalPage) {
  const itemRef = useRef();
  useEffect(() => {
    const options = {
      root: null,
      rootMargin: '0px',
      threshold: 0.1,
    };

    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && hasMore && isSuccess && data) {
        if (curPage < totalPage) {
          setCurPage((prevPage) => prevPage + 1);
        } else {
          setCurPage(totalPage);
        }
      }
    }, options);

    if (observer && itemRef.current) observer.observe(itemRef.current);
    return () => {
      if (observer) {
        observer.disconnect();
      }
    };
  }, [hasMore, isSuccess, data]);
  return { itemRef };
}

export default useObserver;
