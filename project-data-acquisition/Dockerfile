# 使用官方的Python运行时作为父镜像
FROM python:3.8

# 将你的Python项目文件复制到镜像中
COPY . /code

# 设置工作目录
WORKDIR /code

# 安装项目所需的依赖
RUN pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 容器启动时运行的命令
CMD ["python", "run.py"]