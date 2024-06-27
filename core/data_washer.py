from typing import Optional

from core.utils import json_load, FullList, json_dump, find_index
from core.question_model import Question, QuestionModel, QuestionType
from core.importer import ArchiveModel


class DataWasher:

    @staticmethod
    def _merge(q1: Question, q2: Question) -> QuestionModel:
        def my_and(a: Optional[str], b: Optional[str]) -> Optional[str]:
            if a == b:
                return a
            if a is None:
                return b
            if b is None:
                return a
            raise ValueError()

        def my_and_2(a: Optional[str], b: Optional[str]) -> Optional[str]:
            if a is not None and b is not None:
                return f'{a}\n\n此题的其他解释：\n{b}'
            else:
                return my_and(a, b)

        try:
            ans = QuestionModel({
                'answer_idx': q1.data['answer_idx'],
                'choices': q1.data['choices'],
                'type': q1.data['type'],
                'desc': q1.data['desc'],
                # 假定以上内容相同
                'solution': my_and_2(q1.data.get('solution'), q2.data.get('solution')),
                'note': my_and(q1.data.get('note'), q2.data.get('note')),
                'tag': my_and(q1.data.get('tag'), q2.data.get('tag')),
            })
            return ans
        except ValueError:
            vs = f"\n{q1.data}\na.vs.b\n{q2.data}\n"
            print(f"[Warn] 发现大冲突！{vs}")
            return {'a': q1.data, 'b': q2.data}[input(f"合并冲突二选一：(a/b){vs}")]

    @staticmethod
    def export_dedupe_data(folder_path: str, out_path: str):
        ques_map: dict[str, tuple[str, QuestionModel]] = {}
        with FullList(folder_path) as fps:
            for fp in fps:
                obj: ArchiveModel = json_load(fp)
                for ques in obj['questions']:
                    part = obj['part']
                    if ques['desc'] in ques_map:
                        boxed_a = Question(ques)
                        boxed_b = Question(ques_map[ques['desc']][1])
                        if not boxed_a.is_equivalent_to(boxed_b):
                            ques_map[ques['desc']] = (part, DataWasher._merge(boxed_a, boxed_b))
                    else:
                        ques_map[ques['desc']] = (part, ques)
        with open(out_path, 'w') as fp:
            json_dump(DataWasher.final_mapper(ques_map), fp)
        print(f"[Info] 已导出去重后的题目到 {out_path}")

    @staticmethod
    def final_mapper(obj: dict[str, tuple[str, QuestionModel]]) -> list[ArchiveModel]:
        res: list[ArchiveModel] = []
        for k, v in obj.items():
            idx = find_index(res, lambda x: x["part"], v[0])
            if idx == -1:
                res.append({'part': v[0], 'questions': [v[1]]})
            else:
                res[idx]['questions'].append(v[1])
        return res
