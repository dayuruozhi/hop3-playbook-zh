# HOP 3.0 逐篇新建 writer 实测

本实验用三篇中文稿件验证：HOP 3.0 的逐篇子任务能否由宿主驱动层交给新创建、不继承父会话历史的 writer，再将真实生成的报告交回引擎。

## 实测结果

三篇已全部完成。三个不同 writer 分别为 `/root/fresh_writer_01`、`/root/fresh_writer_02`、`/root/fresh_writer_03`，启动均使用 `fork_turns: "none"`。三个 HOP 子实例依次为 `2.1.1`、`2.1.2`、`2.1.3`。每份报告都有六项栏目和四条精确原文引文；均首次提交完成，无重试。父实例最终状态为 `completed`，收集三份报告，逐项与 writer 提交内容一致。核验脚本运行通过。

因此，本宿主中的显式驱动要求可以落地：每次 HOP call 都由驱动实际创建一个新 writer，再回收结果。

## 执行方式

父规约 `work/batch.md` 用 loop + call 调用 `work/review-one.md`，显式要求每篇创建新的 writer。引擎返回 call_protocol，主驱动执行其中的初始化和推进命令。子实例到达 reason 步骤后，驱动只提取当前文章、完整标准、当前指令、输出结构及交付路径，形成 writer 输入包。

主会话随后实际调用宿主的 `collaboration.spawn_agent`，每篇使用不同 agent 名称并设置 `fork_turns: "none"`。writer 只读取指定输入包并自行写出审查报告；主驱动提交该输出，子实例完成检查后将结果回收给父实例，再处理下一篇。没有使用预先写好的报告或质量判定。

`evidence/driver.py` 负责引擎命令和输入包；**新 agent 的启动由主会话通过宿主工具完成**，Python 脚本本身没有 agent 启动器。复用到别的 harness 时，需要实现等价的逐次启动和回收逻辑。这是一次真实执行的驱动适配验证，不是已经发布的通用自动适配器。

## 如何核对

- `evidence/engine.jsonl`：实际执行的命令、完整响应和 stdout/stderr。
- `evidence/agent-launches.json`：主驱动记录的三个 agent 名称、启动参数、输入包及其 SHA256；实际工具调用另见本次会话。
- `evidence/writer-N-packet.json`：第 N 个 writer 收到的业务输入。
- `reports/article-N.json`：writer 实际生成并被提交的完整报告。
- `evidence/child-N-result.json`：各子实例的完成结果。
- `evidence/final-vars.json`：父实例最终变量和收集结果。
- `evidence/verification.json`：完成后运行 `python3 evidence/verify.py` 生成的核验摘要。

## 结论的边界

规约文本没有让 HOP 引擎自动调用 spawn_agent；主驱动读到约束后显式落实了它。`call` 的子状态隔离与 writer 会话历史隔离是两个机制。

本次使用宿主提供的 `fork_turns: "none"` 控制父历史继承。核对记录与父会话标记未传入的观察仅为辅助证据，不是对模型内部状态的独立证明。writer 仍共享宿主的系统指令、工具和文件系统；这不是进程或文件访问沙箱。

引擎检查六项栏目非空、至少两条引文及其确实来自当前稿件。它不独立判定分析深度和结论质量。三篇的集成实验也不能证明比单 agent 更高质量，或证明长批次一定不会退化。

第二个 writer 的原核对记录把“是否继承父对话历史”误填为 true。后续追问中，它说明将本次启动指令及环境信息误当成父历史，并表示未看到此前父消息或其他稿件讨论。原记录未改写，解释单独保存在 `evidence/writer-2-audit-clarification.json`。这也说明自述核对表不能代替宿主启动参数作为证据。
