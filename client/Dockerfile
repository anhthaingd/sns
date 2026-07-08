FROM node:20-bookworm-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173
# Vite dev server, bind 0.0.0.0 để truy cập được từ ngoài container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
