import json
from abc import abstractmethod, ABC
from typing import TextIO, Callable

from core.importer import ArchiveModel
from core.question_model import Question


def json_dump(obj, fp: TextIO):
    return json.dump(obj, fp, ensure_ascii=False, indent="    ")


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
    desc_modifier: Callable[[str], str] = None

    # 描述修改器，用于后处理题目描述，留空则使用默认修改器
    @staticmethod
    def _desc_modifier(desc: str):
        if ExcelExporter.desc_modifier is not None:
            return ExcelExporter.desc_modifier(desc)
        # else: default modifier
        if desc.startswith("<p>") and desc.endswith("</p>"):
            desc = desc[3:-4]
        if True:
            desc = desc.replace("&nbsp;", " ")
        return desc

    @staticmethod
    def export(in_fp: TextIO, out_fp: TextIO, to_file: bool = True):
        model: ArchiveModel = json.load(in_fp)
        result = []

        for ques_model in model["questions"]:
            ques = Question(ques_model)
            temp = {
                "来源": model['part'],
                "描述": ExcelExporter._desc_modifier(ques.get_desc()),
                "选项": "\n".join(ques.get_choices_str_set()),
                "正确答案": "\n".join(ques.get_answer_str_set()),
                "解释": ques.data.get("solution", "无")
            }
            result.append(temp)

        print(f"[log] 已完成 {model['part']} 的数据处理")
        if to_file:
            json_dump(result, out_fp)
            return None
        return result

    @classmethod
    def export_many(cls, in_fps: list[TextIO], out_fp: TextIO):
        res = []
        for fp in in_fps:
            res.extend(ExcelExporter.export(fp, out_fp, to_file=False))
        json_dump(res, out_fp)
