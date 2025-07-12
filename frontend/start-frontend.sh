#!/bin/bash

echo "清理占用端口3000的进程..."
pids=$(lsof -t -i :3001)
if [ -n "$pids" ]; then
  echo "找到占用端口3001的进程，PID: $pids，正在杀死..."
  kill -9 $pids
else
  echo "端口3001未被占用"
fi

echo "等待端口释放..."
sleep 2

echo "启动前端服务，绑定到所有网络接口..."
export HOST=0.0.0.0
export PORT=3001

npm run dev -- --host 0.0.0.0 --port 3001 --strictPort
