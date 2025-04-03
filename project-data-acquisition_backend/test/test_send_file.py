import requests
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Flask 应用运行的 URL 和端口（默认是 127.0.0.1:5000）
url = 'http://127.0.0.1:5000/SaveFile'
data = {"equipment": "A2202020122210041"}

# 监控的文件夹路径
watch_folder = 'test'


class UploaderHandler(FileSystemEventHandler):
    def __init__(self, url, data):
        super().__init__()
        self.url = url
        self.data = data
        self.uploaded_files = set()  # 用于记录已上传的文件，防止重复上传

    def on_modified(self, event):
        if event.is_directory:
            return None
        elif event.src_path.endswith(('.xlsx', '.xls')):  # 仅处理 Excel 文件
            if event.src_path not in self.uploaded_files:
                self.upload_file(event.src_path)
                self.uploaded_files.add(event.src_path)

    def upload_file(self, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(self.url, files=files, data=self.data)
            if response.status_code == 200:
                print(f"File {file_path} uploaded successfully.")
            else:
                print(f"Failed to upload file {file_path}. Status code: {response.status_code}")
                print(response.json())


def start_watching():
    event_handler = UploaderHandler(url, data)
    observer = Observer()
    observer.schedule(event_handler, watch_folder, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)  # 睡眠1秒，减少CPU使用率
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_watching()