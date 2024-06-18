import json
import os.path
from typing import TextIO, TypedDict, Literal

from core.question_model import QuestionModel


class ArchiveModel(TypedDict):
    part: str
    questions: list[QuestionModel]


class SummaryModel(TypedDict):
    max_score: int
    score: int
    max_rank: int
    rank: int


class TampermonkeyDumpModel(TypedDict):
    summary: SummaryModel
    validated: bool
    testId: str
    answerId: str
    content: list[QuestionModel]


class Importer:
    _id_map: dict = {}
    show_incomplete_score_tag = True

    @staticmethod
    def _force_output(path, result) -> Literal[True]:
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        with open(path, "w") as fp:
            json.dump(result, fp, ensure_ascii=False, indent="    ")
        print(f"输出完成至：{path}")
        return True

    @staticmethod
    def _unshell_for_tampermonkey(obj: TampermonkeyDumpModel) \
            -> tuple[list[QuestionModel], str]:
        suggest_filename: str = ""
        id_map = Importer.get_id2title_map()
        # 若 summary 结构不完整，则有 0 != None，也会标记为未验证
        if obj["summary"].get("score", 0) != obj["summary"].get("max_score"):
            print("[Warn] 此数据并未取得满分，注意存在错误！")
            if Importer.show_incomplete_score_tag:
                suggest_filename += "[未满分]"
        if obj["testId"] not in id_map:
            print("[Warn] 无法识别此数据的 testId，请检查数据来源！")
            suggest_filename += f"[ID={obj["testId"]}]"
        else:
            suggest_filename += id_map[obj["testId"]]
        return obj["content"], suggest_filename

    @staticmethod
    def get_id2title_map() -> dict:
        if len(Importer._id_map) != 0:
            return Importer._id_map
        # else:
        try:
            with open("./core/config-id2title.json") as fp:
                Importer._id_map = json.load(fp)
        except FileNotFoundError:
            print("[Warn] 数据文件 config-id2title.json 不存在！")
            Importer._id_map = {}
        return Importer._id_map

    @staticmethod
    def from_json_file(fp: TextIO, overwrite=False, ask=False) -> bool:
        part: str | None = None
        result: ArchiveModel
        raw_obj = json.load(fp)

        if "summary" in raw_obj and "testId" in raw_obj:
            # 数据来自油猴脚本时
            print("[Log] 此数据来自油猴“北化在线测试 Dumper.js”")
            questions, part = Importer._unshell_for_tampermonkey(raw_obj)
        else:
            # 数据为纯 question 数组
            questions = raw_obj

        if part is None:
            part: str = input("请输入题目所属章节名称：")
            if part == "": raise ValueError("无效的章节名称！")
        result = {"part": part, "questions": questions}

        path = f"./archive/questions/{result["part"]}.json"
        if not overwrite and os.path.exists(path):
            if ask:
                if input("文件已存在，是否覆盖？(y/n)") == "y":
                    return Importer._force_output(path, result)
                else:
                    print("[Log] 已取消")
                    return False
            print("[Warn] 文件已存在，保存失败！若要覆盖请使 overwrite = True")
            return False
        return Importer._force_output(path, result)

    @staticmethod
    def from_list_of_files(fps: list[TextIO]):
        for fp in fps:
            Importer.from_json_file(fp)
