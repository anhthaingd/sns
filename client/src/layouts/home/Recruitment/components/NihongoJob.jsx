import React, { useEffect, useRef, useState } from 'react';
import './style.css';
function NihongoJob() {
  const [crawlData, setCrawlData] = useState([]);
  const [crawlDataCSS, setCrawlDataCSS] = useState();
  const [nextData, setNextData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState(null);
  const [curPage, setCurPage] = useState(1);
  const itemRef = useRef();
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(
          `http://localhost:3000/crawl/nihongo?curPage=${curPage}`,
          {
            method: 'GET',
          }
        );
        if (!res.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await res.json();
        setNextData([...data?.html]);
        setCrawlData((prevData) => {
          return [...new Set([...prevData, ...data?.html])];
        });
        data?.html?.length > 0 && setCrawlDataCSS(data?.css);
        setLoading(false);
      } catch (error) {
        setError(error);
        setLoading(false);
      }
    };
    fetchData();
  }, [curPage]);
  useEffect(() => {
    const options = {
      root: null,
      rootMargin: '0px',
      threshold: 0.1,
    };

    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && hasMore) {
        setCurPage((prevPage) => prevPage + 1);
      }
    }, options);

    if (observer && itemRef.current) observer.observe(itemRef.current);
    return () => {
      if (observer) {
        observer.disconnect();
      }
    };
  }, [hasMore]);
  useEffect(() => {
    if (!loading && nextData.length === 0) {
      setHasMore(false);
    }
  }, [hasMore, nextData, loading]);
  return (
    <div>
      <style>{crawlDataCSS}</style>
      {!loading && crawlData?.length > 0 && (
        <ul className='relative job-list__jobs flex flex-col gap-8'>
          {crawlData?.map((c, index) => {
            return (
              <li
                className='border border-neutral-300 dark:border-neutral-600 rounded-sm'
                key={index}
                dangerouslySetInnerHTML={{ __html: c }}
              ></li>
            );
          })}
        </ul>
      )}
      {!loading && crawlData?.length === 0 && (
        <div className='w-full text-2xl font-bold flex justify-center items-center'>
          <p>No Data Yet!</p>
        </div>
      )}
      {hasMore && (
        <p ref={itemRef} className='w-full text-center font-bold'>
          Loading more...
        </p>
      )}
    </div>
  );
}

export default NihongoJob;
