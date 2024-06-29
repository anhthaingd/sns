import React, { useRef } from 'react';
import { useReactToPrint } from 'react-to-print';
import {
  FaCakeCandles,
  FaEnvelope,
  FaLocationDot,
  FaPhone,
  FaGithub,
} from 'react-icons/fa6';
import { format } from 'date-fns';
import { vi } from 'date-fns/locale';
function Template1({ resume }) {
  const componentRef = useRef();
  const handlePrint = useReactToPrint({
    content: () => componentRef.current,
    documentTitle: `${resume?.name}-CV-${resume?.position}`,
  });
  return (
    <>
      <div ref={componentRef}>
        <div className='bg-white text-neutral-800 font-medium p-4 flex flex-col gap-6 rounded'>
          <div className='border-2 border-neutral-300 p-4 flex flex-col gap-4'>
            <div className='p-2 flex flex-col items-center gap-4 border-b-2 border-neutral-300'>
              <h1 className='text-4xl font-bold tracking-widest uppercase'>
                {resume?.name}
              </h1>
              <span className='w-full relative before:w-[96px] before:h-[2px] before:absolute before:bg-neutral-200 before:-translate-x-1/2 before:left-1/2 before:-translate-y-1/2 before:top-1/2'></span>
              <p className='text-2xl font-bold tracking-widest'>
                {resume?.position}
              </p>
            </div>
            <div className='grid grid-cols-5 gap-4 py-4'>
              <div className='col-span-2 flex flex-col gap-4'>
                <div className='flex flex-col gap-4 pb-6 border-b border-neutral-300'>
                  <h2 className='text-2xl font-bold'>Contact</h2>
                  <div className='flex flex-col gap-2'>
                    {resume?.birthday && (
                      <div className='flex items-center gap-2'>
                        <div className='p-2 rounded-full bg-neutral-800 flex justify-center items-center'>
                          <FaCakeCandles className='text-neutral-50' />
                        </div>
                        <p className='font-medium'>
                          {format(new Date(resume?.birthday), 'dd/MM/yyyy', {
                            locale: vi,
                          })}
                        </p>
                      </div>
                    )}
                    <div className='flex items-center gap-2'>
                      <div className='p-2 rounded-full bg-neutral-800 flex justify-center items-center'>
                        <FaEnvelope className='text-neutral-50' />
                      </div>
                      <p className='font-medium'>{resume?.email}</p>
                    </div>
                    <div className='flex items-center gap-2'>
                      <div className='p-2 rounded-full bg-neutral-800 flex justify-center items-center'>
                        <FaPhone className='text-neutral-50' />
                      </div>
                      <p className='font-medium'>{resume?.phone}</p>
                    </div>
                    <div className='flex items-center gap-2'>
                      <div className='p-2 rounded-full bg-neutral-800 flex justify-center items-center'>
                        <FaLocationDot className='text-neutral-50' />
                      </div>
                      <p className='font-medium'>{resume?.address}</p>
                    </div>
                    {resume?.github && (
                      <div className='flex items-center gap-2'>
                        <div className='p-2 rounded-full bg-neutral-800 flex justify-center items-center'>
                          <FaGithub className='text-neutral-50' />
                        </div>
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
                </div>
                {resume?.skills?.length > 0 && (
                  <div className='flex flex-col gap-4 pb-6 border-b border-neutral-300'>
                    <h2 className='text-2xl font-bold'>Skills</h2>
                    <div className='flex flex-col gap-2'>
                      {resume?.skills?.map((s, index) => {
                        return (
                          <p className='w-full text-wrap' key={index}>
                            -{s}
                          </p>
                        );
                      })}
                    </div>
                  </div>
                )}
                {resume?.languages?.length > 0 && (
                  <div className='flex flex-col gap-4 pb-6 border-b border-neutral-300'>
                    <h2 className='text-2xl font-bold'>Languages</h2>
                    <div>
                      {resume?.languages?.map((l, index) => {
                        return (
                          <p className='w-full text-wrap' key={index}>
                            -{l}
                          </p>
                        );
                      })}
                    </div>
                  </div>
                )}
                <div className='flex flex-col gap-4 pb-6 border-b border-neutral-300'>
                  <h2 className='text-2xl font-bold'>Education</h2>
                  <div>
                    <p className='font-bold text-lg'>{resume?.educationName}</p>
                    <p>{resume?.educationMajor}</p>
                    <p>{resume?.educationCompletion}</p>
                    {resume?.educationGPA && <p>GPA: {resume?.educationGPA}</p>}
                  </div>
                </div>
                {resume?.oldCertificates?.length > 0 && (
                  <div className='flex flex-col gap-4 pb-6 border-b border-neutral-300'>
                    <h2 className='text-2xl font-bold'>Certificates</h2>
                    <div>
                      {resume?.oldCertificates?.map((c, index) => {
                        return (
                          <div className='flex items-center gap-2' key={index}>
                            <p>{c?.name}</p>
                            <span>-</span>
                            <a
                              className='text-indigo-500'
                              href={`${import.meta.env.VITE_BACKEND_URL}/${
                                c?.url
                              }`}
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
              <div className='col-span-3 flex flex-col gap-4 px-4 border-l border-neutral-300'>
                <div className='flex flex-col gap-4 pb-6 border-b border-neutral-300'>
                  <h2 className='text-2xl font-bold'>Objective</h2>
                  <p>{resume?.objective}</p>
                </div>
                {resume?.experiences?.length > 0 && (
                  <div className='flex flex-col gap-4 pb-6 border-b border-neutral-300'>
                    <h2 className='text-2xl font-bold'>Experience</h2>
                    {resume?.experiences?.map((e, index) => {
                      return (
                        <div key={index} className='w-full flex flex-col gap-2'>
                          <div className='w-full flex justify-between'>
                            <h3 className='text-lg'>{e?.name}</h3>
                            <p className='italic text-sm'>
                              {e?.startTime} - {e?.endTime}
                            </p>
                          </div>
                          <ul className='list-disc px-6'>
                            {e?.position && (
                              <li>
                                <span className='font-bold'>Position</span>:
                                {e?.position}
                              </li>
                            )}
                            {e?.description && (
                              <li>
                                <span className='font-bold'>Description</span>:
                                {e?.description}
                              </li>
                            )}
                          </ul>
                        </div>
                      );
                    })}
                  </div>
                )}
                {resume?.projects?.length > 0 && (
                  <div className='flex flex-col gap-4 pb-6 border-b border-neutral-300'>
                    <h2 className='text-2xl font-bold'>Projects</h2>
                    {resume?.projects?.map((p, index) => {
                      return (
                        <div className='w-full flex flex-col gap-2' key={index}>
                          <div className='w-full flex justify-between'>
                            <h3 className='text-lg'>{p?.name}</h3>
                          </div>
                          <ul className='list-disc px-6'>
                            {p?.tech && (
                              <li>
                                <span className='font-bold'>Tech</span>:{' '}
                                {p?.tech}
                              </li>
                            )}
                            {p?.description && (
                              <li>
                                <span className='font-bold'>Description</span>:
                                {p?.description}
                              </li>
                            )}
                          </ul>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
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

export default Template1;
