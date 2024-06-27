from enum import IntEnum, unique
from typing import TypedDict, NotRequired, Optional, Dict, List


@unique
class QuestionType(IntEnum):
    SINGLE = 1  # 单选
    MULTIPLE = 2  # 多选
    TRUEFALSE = 3  # 判断


class QuestionModel(TypedDict):
    # Base
    desc: str
    type: QuestionType
    choices: list[str]
    answer_idx: int | list[int]
    # Extension
    solution: NotRequired[str]
    note: NotRequired[str]
    tag: NotRequired[str]


class Question:
    data: QuestionModel

    def __init__(self, model: QuestionModel):
        try:
            # TODO: 不完善的数据检验，没检查数据类型
            model["type"] = QuestionType(model["type"])
            assert ("desc" in model
                    and "type" in model
                    and "choices" in model
                    and "answer_idx" in model)
            self.data = model
        except AssertionError:
            raise ValueError(f"给定的 QuestionModel 不符合其类型定义！\n({model})")
        except ValueError:
            raise ValueError(f"给定的 QuestionModel 中的 type 属性无效！\n({model})")

    def is_equivalent_to(self, other: "Question") -> bool:
        sd = self.data
        od = other.data
        return (sd["type"] == od["type"]
                and sd["desc"] == od["desc"]
                and self.get_answer_str_set()
                == other.get_answer_str_set()
                and sd.get("solution") == od.get("solution")
                and sd.get("note") == od.get("note")
                and sd.get("tag") == od.get("tag")
                )

    def get_choices_str_set(self) -> set[str]:
        return {*self.data["choices"]}

    def get_desc(self) -> str:
        return self.data["desc"]

    def get_solution(self) -> Optional[str]:
        return self.data.get("solution")

    def get_answer_str_set(self) -> set[str]:
        data = self.data
        indexes = data["answer_idx"]
        if isinstance(indexes, int):
            # 坑！不可以 set(data["choices"][indexes])，
            # 因为会这样字符串会被拆成单个字符装入集合中
            return {data["choices"][indexes]}
        else:
            return {data["choices"][i] for i in indexes}
