import json
import os
from datetime import date
from typing import TextIO, Callable

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


def get_date_str(compat=False) -> str:
    if compat:
        return date.today().strftime("%Y/%m/%d")
    return date.today().strftime("%Y / %m / %d")


def inserter(source: str, insert: str, pre: str, post: str) -> str:
    # 查找pre的起始位置
    pre_start = source.find(pre)
    if pre_start == -1:
        raise ValueError(f"Pre-text '{pre}' not found in the text.")

    # 查找post的起始位置，并且它必须紧跟在pre之后
    post_start = source.find(post, pre_start)
    if post_start == -1:
        raise ValueError(f"Post-text '{post}' not found after pre-text '{pre}' in the text.")

    # 在指定位置插入content
    insert_index = pre_start + len(pre)
    return source[:insert_index] + insert + source[post_start:]


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
