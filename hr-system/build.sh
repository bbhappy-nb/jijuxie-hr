#!/bin/bash
# Render 构建脚本：安装依赖 + 构建前端 + 复制到后端

set -e

echo "===== 安装后端依赖 ====="
cd backend
pip install -r requirements.txt
cd ..

echo "===== 安装前端依赖并构建 ====="
cd frontend
npm install
npm run build
cd ..

echo "===== 复制前端文件到后端 ====="
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

echo "===== 构建完成 ====="
