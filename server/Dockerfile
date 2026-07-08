# Image Puppeteer chính thức: đã kèm Chrome + đầy đủ thư viện hệ thống,
# khởi chạy ổn định trong container (bản chromium apt bị SIGTRAP trên arm64).
# Tag khớp đúng version puppeteer trong package-lock (22.10.0) -> Chrome cùng bản.
FROM ghcr.io/puppeteer/puppeteer:22.10.0

# base image chạy sẵn user "pptruser"; đặt app trong home của user đó
WORKDIR /home/pptruser/app

COPY --chown=pptruser:pptruser package*.json ./
RUN npm install

COPY --chown=pptruser:pptruser . .

EXPOSE 3000
CMD ["node", "server.js"]
