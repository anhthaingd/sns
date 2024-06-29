import { intlFormat } from 'date-fns';
export const formatDate = (date) => {
  const result = date
    ? intlFormat(
        new Date(date),
        { year: 'numeric', month: 'long', day: 'numeric' },
        { locale: 'vi' }
      )
    : '';
  return result;
};
