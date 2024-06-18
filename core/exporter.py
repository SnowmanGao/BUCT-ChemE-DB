import re
from abc import abstractmethod, ABC
from typing import TextIO, Callable

from core.importer import ArchiveModel
from core.question_model import Question, QuestionModel
from core.utils import json_dump, json_load


def _desc_mod_for_excel(desc: str):
    """默认的题目描述修改器，用于输出 Excel 文档"""
    if desc.startswith("<p>") and desc.endswith("</p>"):
        desc = desc[3:-4]
    if True:
        desc = desc.replace("&nbsp;", " ")
    return desc


def _desc_mod_for_md(desc: str):
    """默认的题目描述修改器，用于输出 Markdown 文档"""
    desc = re.sub(r"#\[!(.*)]", "![$0.png](../archive/solutions/figures/$0.png)", desc)
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


class Exporter(ABC):
    @staticmethod
    @abstractmethod
    def export(in_fp: TextIO, out_fp: TextIO):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def export_many(cls, in_fps: list[TextIO], out_fp: TextIO):
        for in_fp in in_fps:
            cls.export(in_fp, out_fp)


class ExcelExporter(Exporter):
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


class MarkdownExporter(Exporter):
    desc_modifier: Callable[[str], str] = _desc_mod_for_md
    choice_modifier: Callable[[str], str] = _choice_mod_for_md

    @staticmethod
    def _choice_normalize(ques: QuestionModel):
        temp = ques["answer_idx"]
        return [temp] if isinstance(temp, int) else temp

    @staticmethod
    def export(in_fp: TextIO, out_fp: TextIO, to_file=True):
        obj: ArchiveModel = json_load(in_fp)
        return MarkdownExporter.export_obj(obj, out_fp, to_file)

    @staticmethod
    def export_obj(obj: ArchiveModel, out_fp: TextIO, to_file=True):
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
                    mprint(f"\n> 解释：\n>\n> {ques["solution"].replace('\n', '\n>\n> ')}")
            mprint("\n---\n")
        if to_file:
            print(f"[log] 已完成对 {obj["part"]} 的 Markdown 导出")
            out_fp.write("".join(res))
            return None
        return "".join(res)

    @classmethod
    def export_many(cls, in_fps: list[TextIO], out_fp: TextIO):
        out = []
        for fp in in_fps:
            out.append(MarkdownExporter.export(fp, out_fp, to_file=False))
        out_fp.write("\n\n\n\n".join(out))
        print(f"[log] 已完成对 {len(in_fps)} 个文件的 Markdown 导出")

    @classmethod
    def export_many_objs(cls, objs: list[ArchiveModel], out_fp: TextIO):
        out = []
        for obj in objs:
            out.append(MarkdownExporter.export_obj(obj, out_fp, to_file=False))
        out_fp.write("\n\n\n\n".join(out))
        print(f"[log] 已完成对 {len(objs)} 个文件的 Markdown 导出")
