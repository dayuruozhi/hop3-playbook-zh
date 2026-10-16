# Spec: 每篇由新写作 agent 完成审查
Id: fresh-writer-batch
Goal: 对三篇稿件逐篇调用单篇审查子规约，由驱动层为每次调用创建一个不继承父对话历史的新写作 agent，收集其真实生成的报告。

## Inputs
- source_path % line
- rubric % text

## Outputs
- reviews % [yaml]

## Constraints
- 每次 review-one 调用都必须创建新的写作 agent，不可把同一 agent 用于不同文章。
- 新写作 agent 只接收当前文章、完整审查要求和本子实例的当前待办，不接收前面文章的报告。
- 新 agent 的创建及不继承父历史由驱动层落实，并单独记录，不把子实例状态隔离冒充模型上下文隔离。

## Steps
1. [act] 读取稿件列表
  - ← source_path
  + → articles % [yaml]
  > ```hop_python
  > articles = parse_json(read(path: source_path))
  > ```
2. [loop for-each article in articles, collect review into reviews] 每篇调用一次独立写作任务
  + → reviews % [yaml]
  2.1. [call review-one(article: article, rubric: rubric)] 驱动层须为本次调用创建新写作 agent
    + → review: report
