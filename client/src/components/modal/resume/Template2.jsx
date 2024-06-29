import React, { useMemo, useRef } from 'react';
import { useReactToPrint } from 'react-to-print';
import {
  FaCakeCandles,
  FaEnvelope,
  FaSquarePhone,
  FaLocationDot,
  FaGithub,
} from 'react-icons/fa6';
import { format } from 'date-fns';
import { vi } from 'date-fns/locale';
function Template2({ resume }) {
  const componentRef = useRef();
  const handlePrint = useReactToPrint({
    content: () => componentRef.current,
    documentTitle: `${resume?.name}-CV-${resume?.position}`,
  });
  const splitName = useMemo(() => {
    return (
      resume.name.split(' ')[0].split('')[0],
      resume.name.split(' ')[resume.name.split(' ').length - 1].split('')[0]
    );
  }, [resume]);
  return (
    <>
      <div
        className='relative grid grid-cols-3 p-4 bg-white text-neutral-800'
        ref={componentRef}
      >
        <div className='absolute mt-4 bg-neutral-500 w-full py-8 tracking-[8px] grid grid-cols-3'>
          <div className='col-span-1'></div>
          <div className='col-span-2 flex flex-col justify-center items-center gap-4'>
            <h1 className='text-4xl text-white font-medium uppercase'>
              {resume?.name}
            </h1>
            <p className='text-2xl text-white font-medium'>
              {resume?.position}
            </p>
          </div>
        </div>
        <div className='relative col-span-1 w-full h-full py-8 px-6 bg-orange-200 overflow-hidden flex flex-col gap-8'>
          <div>
            <div className='relative m-auto size-[170px] overflow-hidden'>
              <div className='relative w-full h-full'>
                <img
                  className='w-full h-full object-cover'
                  src={`${import.meta.env.VITE_BACKEND_URL}/${
                    resume?.oldAvatar?.url
                  }`}
                  alt={resume?.oldAvatar?.name}
                />
              </div>
              <span className='absolute w-full top-0 h-[8px] bg-neutral-800 z-10'></span>
              <span className='absolute w-full bottom-0 h-[8px] bg-neutral-800 z-10'></span>
              <span className='absolute h-full l-0 top-0 w-[8px] bg-neutral-800 z-10'></span>
              <span className='absolute h-full right-0 top-0 w-[8px] bg-neutral-800 z-10'></span>
              <span className='absolute size-[84px] border-b-[8px] border-neutral-800 z-20 right-0 top-0 rotate-45 translate-x-[52%] -translate-y-[50%] bg-orange-200'></span>
              <span className='absolute size-[84px] border-t-[8px] border-neutral-800 z-20 bottom-0 rotate-45 -translate-x-[53%] translate-y-[52%] bg-orange-200'></span>
            </div>
          </div>
          <div className='flex flex-col gap-2'>
            {resume?.birthday && (
              <div className='flex items-center gap-2'>
                <FaCakeCandles />
                <p className='font-medium'>
                  {format(new Date(resume?.birthday), 'dd/MM/yyyy', {
                    locale: vi,
                  })}
                </p>
              </div>
            )}
            {resume?.email && (
              <div className='flex items-center gap-2'>
                <FaEnvelope />
                <p className='font-medium'>{resume?.email}</p>
              </div>
            )}
            {resume?.address && (
              <div className='flex items-center gap-2'>
                <FaLocationDot />
                <p className='font-medium'>{resume?.address}</p>
              </div>
            )}
            {resume?.phone && (
              <div className='flex items-center gap-2'>
                <FaSquarePhone />
                <p className='font-medium'>{resume?.phone}</p>
              </div>
            )}
            {resume.github && (
              <div className='flex items-center gap-2'>
                <FaGithub />
                <a
                  className='font-medium'
                  href={resume?.github}
                  target='_blank'
                  rel='noopener noreferrer'
                >
                  {resume?.github}
                </a>
              </div>
            )}
          </div>
          <div>
            <h2 className='pb-2 border-b border-neutral-500 uppercase tracking-[2px] text-lg font-bold'>
              Skills
            </h2>
            <ul className='flex flex-col gap-2 p-2'>
              {resume?.skills?.map((s, index) => {
                return (
                  <li className='font-medium text-base' key={index}>
                    s
                  </li>
                );
              })}
            </ul>
          </div>
          {resume?.languages.length > 0 && (
            <div>
              <h2 className='pb-2 border-b border-neutral-500 uppercase tracking-[2px] text-lg font-bold'>
                Languages
              </h2>
              <ul className='flex flex-col gap-2 p-2'>
                {resume?.languages?.map((l, index) => {
                  return (
                    <li className='font-medium text-base' key={index}>
                      l
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
          {resume?.oldCertificates.length > 0 && (
            <div>
              <h2 className='pb-2 border-b border-neutral-500 uppercase tracking-[2px] text-lg font-bold'>
                Certificates
              </h2>
              <div className='flex flex-col gap-2 p-2 font-medium'>
                {resume?.oldCertificates?.map((c, index) => {
                  return (
                    <div className='flex items-center gap-2' key={index}>
                      <p>{c?.name}</p>
                      <span>-</span>
                      <a
                        className='text-indigo-500'
                        href={`${import.meta.env.VITE_BACKEND_URL}/${c?.url}`}
                        download={c?.name}
                        target='_blank'
                      >
                        {c?.name}.pdf
                      </a>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
        <div className='col-span-2 pt-[200px] px-4 flex flex-col gap-4'>
          {resume?.objective && (
            <div className='flex flex-col gap-4'>
              <h2 className='uppercase tracking-[6px] text-lg font-bold bg-neutral-200 p-2 text-center'>
                Objective
              </h2>
              <p className='text-medium'>{resume?.objective}</p>
            </div>
          )}
          <div className='flex flex-col gap-4'>
            <h2 className='uppercase tracking-[6px] text-lg font-bold bg-neutral-200 p-2 text-center'>
              Education
            </h2>
            <div className='flex flex-col gap-2'>
              <h3 className='font-bold text-lg uppercase'>
                {resume?.educationName}
              </h3>
              <p className='text-neutral-600 italic'>
                {resume?.educationCompletion}
              </p>
              <p className='font-medium'>{resume?.educationMajor}</p>
              <p>
                GPA: <span className='font-medium'>{resume?.educationGPA}</span>
              </p>
            </div>
          </div>
          {resume?.experiences?.length > 0 && (
            <div className='flex flex-col gap-4'>
              <h2 className='uppercase tracking-[6px] text-lg font-bold bg-neutral-200 p-2 text-center'>
                Experiences
              </h2>
              <div className='flex flex-col gap-2'>
                <div>
                  {resume?.experiences?.map((e, index) => {
                    return (
                      <div className='font-medium' key={index}>
                        <h3 className='font-bold text-lg'>{e?.name}</h3>
                        <p className='italic'>
                          {e?.startTime} - {e?.endTime}
                        </p>
                        <p>{e?.position}</p>
                        <p>Description: {e?.description}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
          {resume?.projects?.length > 0 && (
            <div className='flex flex-col gap-4'>
              <h2 className='uppercase tracking-[6px] text-lg font-bold bg-neutral-200 p-2 text-center'>
                Projects
              </h2>
              <div className='flex flex-col gap-2'>
                <div>
                  {resume?.projects?.map((p, index) => {
                    return (
                      <div className='font-medium' key={index}>
                        <h3 className='font-bold text-lg'>{p?.name}</h3>
                        <p>{p?.tech}</p>
                        <p>Description: {p?.description}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      <div className='w-full flex justify-end px-4'>
        <button
          className='px-4 py-2 bg-blue-500 hover:bg-blue-700 transition-colors text-white font-bold'
          onClick={handlePrint}
        >
          DOWNLOAD
        </button>
      </div>
    </>
  );
}

export default Template2;
