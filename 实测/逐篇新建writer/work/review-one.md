# Spec: 单篇稿件审查
Id: review-one
Goal: 对给定的一篇中文稿件生成有原文依据的六项审查报告。

## Inputs
- article % yaml
- rubric % text

## Outputs
- report % yaml

## Constraints
- 仅审查输入 article，不阅读其他稿件或之前的报告。
- 六项栏目全部提供；原文依据至少两条，每条包含原样引文与具体解读。
- 缺失信息应明确指出，不补造事实，建议与证据相称。

## Steps
1. [subtask retry=1] 写作并核对本篇报告
  + → report % yaml
  1.1. [reason] 根据当前稿件和完整标准生成报告
    - ← article, rubric
    + → report % yaml
    > 阅读 article 和 rubric，独立写作报告，不使用其他文章的报告。
    > report 包含核心判断、原文依据、可取之处、关键缺口、待核实问题、处理建议。原文依据是引文和解读对象的列表，其余字段为文字。
  1.2. [check final] 程序核对六项栏目和原文引文
    - ← article, report
    + → structure_ok % bool
    + → structure_note % text
    > 本检查只核对结构和引文，不宣称验证分析质量。
    > ```hop_python
    > fields = ["核心判断", "原文依据", "可取之处", "关键缺口", "待核实问题", "处理建议"]
    > structure_ok = False
    > structure_note = "请补齐六项栏目和至少两条附解读的真实引文。"
    > if all([field in report for field in fields]):
    >     has_text = all([len(strip(report[field])) > 0 for field in ["核心判断", "可取之处", "关键缺口", "待核实问题", "处理建议"]])
    >     if has_text and count(report["原文依据"]) >= 2:
    >         structure_ok = all(["引文" in item and "解读" in item and len(strip(item["引文"])) > 0 and len(strip(item["解读"])) > 0 and item["引文"] in article["正文"] for item in report["原文依据"]])
    >         structure_note = "结构和原文引文核对通过。" if structure_ok else "引文须为当前文章原文，且每条须有解读。"
    > ```
