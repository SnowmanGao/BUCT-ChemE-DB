import json
import os
from contextlib import contextmanager
from datetime import date
from typing import TextIO, Callable

from overrides import overrides


def json_dump(obj, fp: TextIO):
    """将对象序列化为 JSON 文本，只能写入空文件"""
    json.dump(obj, fp, ensure_ascii=False, indent="    ")


def json_overwrite(obj, fp: TextIO):
    """将对象序列化为 JSON 文本，然后覆写给定文件"""
    fp.seek(0)
    json_dump(obj, fp)
    fp.truncate()


def json_load(fp: TextIO):
    """从 JSON 文件中读取对象"""
    return json.load(fp)


def get_date_str(compat=False) -> str:
    """获取当前日期的字符串表示，例如：2024 / 06 / 27"""
    if compat:
        return date.today().strftime("%Y/%m/%d")
    return date.today().strftime("%Y / %m / %d")


def find_index[T, V](source: list[T], target: V, key: Callable[[T], V]) -> int:
    """
    查找列表中第一个满足条件的元素的索引\n
    Usage:\n
    >>> find_index([-2, -1, 0, 1], 1, abs)
    >>> # Result: 1
    :param source: 要查找的列表
    :param target: 要查找的目标值
    :param key: 从列表元素到目标值的映射函数
    :return: 第一个满足条件的元素的索引，若没有找到则返回 -1
    """
    for idx, item in enumerate(source):
        if key(item) == target:
            return idx
    return -1


def for_each[T](source: list[T], func: Callable[[T], any]) -> None:
    """
    遍历列表中的每个元素，并执行指定的函数
    :param source: 要遍历的列表
    :param func: 要执行的函数
    """
    for item in source:
        func(item)


def inserter(source: str, target: str, pre: str, post: str) -> str:
    """
    在源文本指定的上下文环境中插入目标文本，并返回插入后的字符串
    :param source: 源文本
    :param target: 目标文本
    :param pre: 要求的插入位置之前的文本
    :param post: 要求的插入位置之后的文本
    :return: 插入后的结果文本
    """
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
    return source[:insert_index] + target + source[post_start:]


@contextmanager
def full_list(path: str, option='r'):
    if not os.path.exists(path):
        raise FileNotFoundError(f"[Err] 未找到路径 {path}！")
    if not os.path.isdir(path):
        raise NotADirectoryError(f"[Err] {path} 不是一个有效的路径！")
    handles = []
    for name in os.listdir(path):
        handles.append(open(os.path.join(path, name), option))
    yield handles
    for_each(handles, lambda fp: fp.close())


@contextmanager
def while_list(path: str, *all_words: str, option='r'):
    with full_list(path, option) as handles:
        handles = [i for i in handles if all(j in i.name for j in all_words)]
        yield handles


@contextmanager
def black_list(path: str, *or_words: str, option='r'):
    with full_list(path, option) as handles:
        handles = [i for i in handles if not any(j in i.name for j in or_words)]
        yield handles
