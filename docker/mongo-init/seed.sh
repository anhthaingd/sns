#!/bin/bash
# Tự động seed dữ liệu bắt buộc vào DB `fuurin` khi container mongo khởi tạo lần đầu.
# Các file JSON được mount vào /seed từ ./server/data
set -e

echo "[seed] Importing roles..."
mongoimport --db fuurin --collection roles --jsonArray --drop --file /seed/roles.json

echo "[seed] Importing website config..."
mongoimport --db fuurin --collection webs --jsonArray --drop --file /seed/social_app.webs.json

echo "[seed] Done."
