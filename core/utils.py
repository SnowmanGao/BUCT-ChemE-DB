import os
from typing import TextIO


class FullList:
    def __init__(self, path, option='r'):
        if not os.path.exists(path):
            raise FileNotFoundError(f"[Err] 未找到路径 {path}！")
        if not os.path.isdir(path):
            raise NotADirectoryError(f"[Err] {path} 不是一个有效的路径！")
        self._path = path
        self._option = option
        self._handles = []

    def __enter__(self) -> list[TextIO]:
        for i in os.listdir(self._path):
            self._handles.append(
                open(os.path.join(self._path, i), self._option)
            )
        return self._handles

    def __exit__(self, exc_type, exc_val, exc_tb):
        for i in self._handles:
            i.close()
