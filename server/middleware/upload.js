import multer from 'multer';
import path from 'path';
import fs from 'fs';

// Allowed extensions for images and PDFs
const allowedImageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];
const allowedPdfExtensions = ['.pdf'];

// Middleware for handling both image and PDF uploads
const upload = multer({
  storage: multer.diskStorage({
    destination: (req, file, cb) => {
      const fileExtension = path.extname(file.originalname).toLowerCase();
      let uploadPath = 'public/uploads'; // default path

      if (allowedImageExtensions.includes(fileExtension)) {
        uploadPath = 'public/uploads';
      } else if (allowedPdfExtensions.includes(fileExtension)) {
        uploadPath = 'public/certificates';
      } else {
        return cb(new Error('Invalid file format.'));
      }

      // Create directory if it doesn't exist
      fs.mkdirSync(uploadPath, { recursive: true });
      cb(null, uploadPath);
    },
    filename: (req, file, cb) => {
      const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
      const filename = uniqueSuffix + '-' + file.originalname;
      cb(null, filename);
    },
  }),
  limits: { fileSize: 25 * 1024 * 1024 }, // Limit file size to 25MB
  fileFilter: (req, file, cb) => {
    const fileExtension = path.extname(file.originalname).toLowerCase();
    if (
      allowedImageExtensions.includes(fileExtension) ||
      allowedPdfExtensions.includes(fileExtension)
    ) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file format.'));
    }
  },
});
const uploadSingleFile = multer({
  storage: multer.diskStorage({
    destination: (req, file, cb) => {
      let uploadPath = 'public/uploads/files';
      fs.mkdirSync(uploadPath, { recursive: true });
      cb(null, uploadPath);
    },
    filename: (req, file, cb) => {
      const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
      const filename = uniqueSuffix + '-' + file.originalname;
      cb(null, filename);
    },
  }),
  limits: { fileSize: 25 * 1024 * 1024 }, // Limit file size to 25MB
  fileFilter: (req, file, cb) => {
    cb(null, true);
  },
});
// Middleware for handling both image and PDF uploads
const uploadFields = upload.fields([
  { name: 'images', maxCount: 10 },
  { name: 'avatar', maxCount: 1 },
  { name: 'certificates', maxCount: 10 },
]);
const uploadFile = uploadSingleFile.single('file');
export { uploadFields, uploadFile };
