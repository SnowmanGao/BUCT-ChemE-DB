import json
import os
from typing import TextIO, Callable, Any

from overrides import overrides


def json_dump(obj, fp: TextIO):
    json.dump(obj, fp, ensure_ascii=False, indent="    ")


def json_overwrite(obj, fp: TextIO):
    fp.seek(0)
    json_dump(obj, fp)
    fp.truncate()


def json_load(fp: TextIO):
    return json.load(fp)


def find_index[T, V](li: list[T], key: Callable[[T], V], target: V) -> int:
    for idx, item in enumerate(li):
        if key(item) == target:
            return idx
    return -1


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


class WhiteList(FullList):
    def __init__(self, path, *words: str, option='r'):
        self._words = words
        super().__init__(path, option)

    @overrides
    def __enter__(self) -> list[TextIO]:
        for i in os.listdir(self._path):
            if self._should_block(i):
                continue
            self._handles.append(
                open(os.path.join(self._path, i), self._option)
            )
        return self._handles

    def _should_block(self, text):
        for j in self._words:
            if j in text:
                return False
        return True
