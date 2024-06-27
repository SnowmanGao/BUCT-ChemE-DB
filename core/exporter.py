import re
from abc import abstractmethod, ABC
from typing import TextIO, Callable

from core.importer import ArchiveModel
from core.question_model import Question, QuestionModel
from core.utils import json_dump, json_load, get_date_str


def _desc_mod_for_excel(desc: str):
    """默认的题目描述修改器，用于输出 Excel 文档"""
    if desc.startswith("<p>") and desc.endswith("</p>"):
        desc = desc[3:-4]
    if True:
        desc = desc.replace("&nbsp;", " ")
    return desc


def _desc_mod_for_md(desc: str):
    """默认的题目描述修改器，用于输出 Markdown 文档"""
    desc = re.sub(r"<p>(.*?)</p>", r"\1\n", desc)
    desc = re.sub(r"<img.*?id=([A-Z]+).*?title=\"(.*?)\".*?/>",
                  r"![\1](../archive/cached_pics/\1/\2)", desc)
    desc = desc.replace("<br/>", "\\n")
    desc = desc.replace("~", "\\~")
    desc = desc.replace("*", "\\*")
    desc = desc.replace("^", "\\^")
    return desc


def _choice_mod_for_md(desc: str):
    """默认的题目选项修改器，用于输出 Markdown 文档"""
    desc = desc.replace("~", "\\~")
    desc = desc.replace("*", "\\*")
    desc = desc.replace("^", "\\^")
    return desc


def _solution_mod_for_md(desc: str):
    """默认的题解修改器，用于输出 Markdown 文档"""
    return re.sub(r"#\[!fig(.*)]",
                  "![\\1.png](../archive/solutions/figures/fig\\1.png)", desc)


def _title_mod_for_md():
    """默认的题目描述修改器，用于输出 Markdown 文档"""
    return (f"#  化实 2201 化工原理客观题（丁忠伟）\n\n\n\n版本：{get_date_str()}"
            "\n\n文件信息：{@chars} 字，{@lines} 行\n\n\n\n---\n\n\n\n\n\n")


class ExporterBase(ABC):
    @staticmethod
    @abstractmethod
    def export(in_fp: TextIO, out_fp: TextIO):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def export_many(cls, in_fps: list[TextIO], out_fp: TextIO):
        for in_fp in in_fps:
            cls.export(in_fp, out_fp)


class ExcelExporter(ExporterBase):
    desc_modifier: Callable[[str], str] = _desc_mod_for_excel

    # 描述修改器，用于后处理题目描述，留空则使用默认修改器
    @staticmethod
    def export(in_fp: TextIO, out_fp: TextIO, to_file: bool = True):
        model: ArchiveModel = json_load(in_fp)
        result = []

        for ques_model in model["questions"]:
            ques = Question(ques_model)
            temp = {
                "来源": model['part'],
                "描述": ExcelExporter.desc_modifier(ques.get_desc()),
                "选项": "\n".join(ques.get_choices_str_set()),
                "正确答案": "\n".join(ques.get_answer_str_set()),
                "解释": ques.data.get("solution", "无")
            }
            result.append(temp)

        if to_file:
            print(f"[log] 已完成对 {model['part']} 的 Excel 导出")
            json_dump(result, out_fp)
            return None
        return result

    @classmethod
    def export_many(cls, in_fps: list[TextIO], out_fp: TextIO):
        res = []
        for fp in in_fps:
            res.extend(ExcelExporter.export(fp, out_fp, to_file=False))
        json_dump(res, out_fp)
        print(f"[log] 已完成对 {len(in_fps)} 个文件的 Excel 导出")


class MarkdownExporter(ExporterBase):
    desc_modifier: Callable[[str], str] = _desc_mod_for_md
    choice_modifier: Callable[[str], str] = _choice_mod_for_md
    title_modifier: Callable[[], str] = _title_mod_for_md
    solution_modifier: Callable[[str], str] = _solution_mod_for_md

    @staticmethod
    def _choice_normalize(ques: QuestionModel):
        temp = ques["answer_idx"]
        return [temp] if isinstance(temp, int) else temp

    @staticmethod
    def export(in_fp: TextIO, out_fp: TextIO, is_to_file=True):
        """
        将某个关卡的题目 JSON 文件导出为 Markdown 文档。
        :param in_fp: 要读取的关卡 JSON 文件
        :param out_fp: 要输出到的 Markdown 文档
        :param is_to_file: 结果是否直接写入文件，默认为 True
        :return: 若 is_to_file 为 True，则返回 None，否则返回生成的 Markdown 字符串
        """
        obj: ArchiveModel = json_load(in_fp)
        return MarkdownExporter.export_obj(obj, out_fp, is_to_file)

    @staticmethod
    def export_obj(obj: ArchiveModel, out_fp: TextIO, is_to_file=True):
        """
        将某个关卡对象导出为 Markdown 文档。
        :param obj: 要读取的关卡对象（TypedDict）
        :param out_fp: 要输出到的 Markdown 文档
        :param is_to_file: 结果是否直接写入文件，默认为 True
        :return: 若 is_to_file 为 True，则返回 None，否则返回生成的 Markdown 字符串
        """
        res: list[str] = []
        mprint = lambda x: res.append(x + "\n")

        mprint(f"# {obj["part"]}\n")
        for ques in obj["questions"]:
            desc = MarkdownExporter.desc_modifier(ques['desc'])
            ans_idx = MarkdownExporter._choice_normalize(ques)
            mprint(f"\n\n#### {desc}\n")
            for idx, choice in enumerate(ques["choices"]):
                choice = MarkdownExporter.choice_modifier(choice)
                mprint(f"- [{'x' if idx in ans_idx else ' '}] {choice}")
            if "solution" in ques:
                if ques["solution"] is not None:
                    solution = MarkdownExporter.solution_modifier(ques["solution"])
                    mprint(f"\n> 解释：\n>\n> {solution.replace('\n', '\n>\n> ')}")
            mprint("\n---\n")
        if is_to_file:
            print(f"[log] 已完成对 {obj["part"]} 的 Markdown 导出")
            out_fp.write("".join(res))
            return None
        return "".join(res)

    @classmethod
    def export_many(cls, in_fps: list[TextIO], out_fp: TextIO):
        """
        将多个关卡的题目 JSON 文件导出为一个 Markdown 文档。
        :param in_fps: 要读取的关卡 JSON 文件列表
        :param out_fp: 要输出到的 Markdown 文档
        """
        out = [MarkdownExporter.title_modifier()]
        for fp in in_fps:
            out.append(MarkdownExporter.export(fp, out_fp, is_to_file=False))
        out_fp.write("\n\n\n\n".join(out))
        print(f"[log] 已完成对 {len(in_fps)} 个文件的 Markdown 导出")

    @classmethod
    def export_many_objs(cls, objs: list[ArchiveModel], out_fp: TextIO):
        """
        将多个关卡对象导出为一个 Markdown 文档。
        :param objs: 要读取的关卡对象（TypedDict）列表
        :param out_fp: 要输出到的 Markdown 文档
        """
        out = [MarkdownExporter.title_modifier()]
        for obj in objs:
            out.append(MarkdownExporter.export_obj(obj, out_fp, is_to_file=False))
        out_fp.write("\n\n\n\n".join(out))
        print(f"[log] 已完成对 {len(objs)} 个文件的 Markdown 导出")
