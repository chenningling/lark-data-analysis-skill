---
name: lark-data-analysis-report
description: "当用户提供一个或多个 Excel/CSV 表格，要求进行业务数据分析，并将分析过程、计算结果、可视化看板和图文分析报告沉淀到飞书中时使用。该技能会创建飞书多维表格作为数据分析过程记录仓库，按原子步骤写入数据表和结果表，建立飞书 Base 仪表盘，并创建飞书云文档报告引用对应的多维表格产物。"
metadata:
  requires:
    bins: ["lark-cli"]
  cliHelp: "lark-cli base --help && lark-cli docs --help"
---

# 飞书数据分析报告沉淀

## 使用边界

使用本技能处理这些请求：

- 用户提供一个或多个 `.xlsx`、`.xls`、`.csv`、`.tsv` 文件，并要求做数据分析。
- 用户希望把分析过程、口径、计算表、结果表、看板、报告沉淀到飞书。
- 用户要求可追溯、可调整、可复核的数据分析产物。
- 用户要求最终返回飞书云文档和飞书多维表格链接。

不要只给口头结论；本技能的完成标准是：本地分析完成、飞书 Base 记录过程、Base 仪表盘可查看、飞书 Doc 报告可阅读并引用 Base。

## 先读哪些参考

按任务阶段渐进读取，避免一次性加载全部文档：

- 开始前：读 [`references/auth-and-permission.md`](references/auth-and-permission.md)。
- 分析设计：读 [`references/analysis-playbook.md`](references/analysis-playbook.md)。
- Base 建模与写入：读 [`references/base-modeling.md`](references/base-modeling.md)，再按需读 `lark-base-*.md` 原子命令文档；涉及默认字段改造时读 `lark-base-field-update.md`、`lark-base-field-delete.md` 和 `lark-base-view-set-visible-fields.md`。
- 看板：读 [`references/lark-base-dashboard.md`](references/lark-base-dashboard.md)、[`references/lark-base-dashboard-block-create.md`](references/lark-base-dashboard-block-create.md)、[`references/dashboard-block-data-config.md`](references/dashboard-block-data-config.md)。
- 图文报告：读 [`references/report-template.md`](references/report-template.md)、[`references/visual-reporting.md`](references/visual-reporting.md)、[`references/lark-doc-create.md`](references/lark-doc-create.md)，需要追加或修订时读 [`references/lark-doc-update.md`](references/lark-doc-update.md)。
- 原始数据与溯源：读 [`references/raw-data-and-lineage.md`](references/raw-data-and-lineage.md)，单个 Excel/CSV 优先使用 [`references/lark-drive-import.md`](references/lark-drive-import.md)。

## 标准作业流程

1. **确认输入与目标**
   - 识别所有用户提供的 Excel/CSV 文件、表单页、字段含义、分析问题和产出位置。
   - 如果用户没有指定飞书文件夹或知识库位置，默认创建在当前账号个人空间根目录。
   - 写入飞书属于创建资源，若用户本轮已经明确要求“开发/创建/写入到飞书”，可继续执行；若只是探索方案，先不要创建资源。

2. **本地读取与数据体检**
   - 用 Python/pandas、Excel skill 或其他可靠结构化工具读取文件，不要靠文本猜表格内容。
   - 可先运行 `scripts/profile_excel.py` 生成字段画像、缺失值、数值分布、样本行和建议分析方向。
   - 记录每个输入表的来源文件、工作表名、行数、字段数、主键候选、时间字段候选、金额/数量/状态/分类字段候选。

3. **创建或选择分析过程仓库**
   - 单个 Excel/CSV：优先用 `lark-cli drive +import --type bitable` 导入为飞书 Base，把导入得到的原始数据表作为仓库的原始事实表，再追加过程表、结果表、看板和报告。
   - 多个文件/工作表：若无法一次导入到同一 Base，创建新的飞书多维表格，命名建议：`数据分析过程记录仓库-<主题>-<日期>`，并把默认 `数据表` 重命名/改造成第一张原始数据表；其余文件/工作表另建 `原始数据_<来源>` 表。
   - 不要保留空白默认 `数据表`。如果创建 Base 后出现默认空表，必须读取表列表并复用或重命名它。
   - 默认表的默认字段不能空置在最前面：优先把默认主字段改名为第一业务主键字段并直接写入；能删除的默认字段删除，接口限制不能删除的字段必须在视图中隐藏，或从建表阶段通过 `fields` 一次性覆盖字段结构。

4. **设计过程表与溯源关系**
   - 至少创建这些子表：
     - `00_输入数据目录`：每个文件/工作表一行，记录来源、行列数、时间范围、备注。
     - `01_字段字典与质量检查`：字段名、类型、缺失率、唯一值数、异常值说明。
     - `02_分析问题与指标口径`：用户问题、指标定义、过滤条件、计算公式、口径解释。
     - `03_清洗转换步骤`：步骤编号、输入表、处理动作、原因、输出表、影响行数。
     - `04_核心明细或宽表`：经过清洗、合并、派生后的可复核分析底表。
     - `05_聚合结果表`：按业务维度聚合后的结果。
     - `06_洞察与行动建议`：结论、证据表、影响程度、建议动作、优先级。
   - 根据实际分析添加原子结果表，例如 `渠道ROI分析`、`区域销售排名`、`客户分层结果`、`异常订单清单`。

   - 原始数据表必须保留业务主键或生成 `源记录键`，例如订单 ID、用户 ID、文件名+行号。
   - 结果表与过程表要记录 `来源表`、`来源字段`、`来源筛选条件`、`来源行数`、`对应原始记录范围`。
   - 能建立明确一对一/一对多关系时，可创建 Base `link` 关联字段，把结果或异常明细关联回原始记录；聚合表行数过大时，不强行关联全部原始行，改用来源条件和视图链接溯源。

5. **写入 Base**
   - 先读 `lark-base-base-create.md` 创建 Base。
   - 每张子表先用 `lark-base-table-create.md` 建表；字段较复杂时先建最小表，再用 `lark-base-field-create.md` 补字段。
   - 写记录前必须读 `lark-base-shortcut-record-value.md`，再用 `lark-base-record-batch-create.md` 分批写入；单批不超过 200 行。
   - 表名、字段名使用中文且稳定，保留步骤编号，便于用户后续指令精确引用。

   - 如果使用 `drive +import --type bitable`，导入完成后用 `+table-list` 找到原始表，并在原始表上创建“全部原始数据”“有效订单”“退款订单”“异常明细”等视图。
   - 如果使用 `+base-create`，先用 `+table-list` 找到默认 `数据表`，再用 `+table-update` 重命名为原始表或直接写入第一批原始数据。写入前必须完成默认字段处理：复用默认主字段、删除可删默认字段、隐藏不可删且无业务意义的字段。

6. **创建看板**
   - 用 `lark-base-dashboard-create.md` 创建仪表盘，名称建议：`数据分析看板-<主题>`。
   - 串行创建组件，禁止并发创建 dashboard block。
   - 图表必须服务于结论：指标卡看总量/均值/转化率，折线图看趋势，柱状/条形看排名，饼图/环形看结构占比，散点图看相关关系，漏斗图看转化路径。
   - 组件完成后可用 `lark-base-dashboard-arrange.md` 自动重排。

7. **生成飞书图文报告**
   - 报告标题建议：`<主题>数据分析报告`。
   - 报告必须包含：摘要、数据来源、口径说明、分析过程索引、关键发现、图表解读、可执行建议、风险与后续追踪。
   - 图表必须跟随对应结论出现：每个关键发现内采用“结论 -> 图表 -> 证据 -> 建议”的结构，不要把全部图片或白板集中追加到文档末尾。
   - 每个图表必须和一个 Base 结果表或看板组件对应，图表标题或图注中写清楚“对应 Base 表/看板组件”。
   - 优先在文档中插入白板图表：`docs +create/+update` 在对应关键发现附近创建空白画板，读取 `board_tokens`，再用 `lark-cli whiteboard +update` 填充内容。
   - 需要精确样式控制时优先使用飞书白板 DSL，经 `whiteboard-cli` 转为 OpenAPI raw 后写入；`whiteboard-cli` 不可用时，简单结构图可用 Mermaid，复杂经营图退回本地 PNG，但必须保留 Base 看板作为交互式来源。
   - 文档中的每个关键数字或图表结论，都要引用对应 Base 子表、看板或结果表。可使用 Markdown 链接、Base 链接、或 `<mention-doc token="..." type="bitable">...</mention-doc>` 引用多维表格。
   - 不要在报告里塞满原始明细；明细留在 Base，文档只呈现可读解释和可行动结论。

8. **最终交付**
   - 返回飞书文档链接、飞书多维表格链接、看板名称或链接、以及关键产物清单。
   - 简要说明本次分析的主要结论、可追溯表名、后续可调整的分析步骤编号。

## 质量标准

- 结论必须“有证据”：每条洞察绑定一个结果表或看板组件。
- 图表必须“有对应”：文档内每个白板/图片图表都绑定同源 Base 结果表或 dashboard block。
- 过程必须“原子化”：用户能指出某个步骤让 Agent 重算或修改。
- 溯源必须“可回跳”：核心过程表、异常明细和结果表能通过关联字段、来源键、筛选条件或视图链接回到原始数据。
- 指标必须“可解释”：所有指标都有口径、过滤条件、计算字段和边界说明。
- 建议必须“可落地”：给出负责人视角的动作、优先级、预期影响和验证指标。
- 链接必须“可打开”：最终回复中明确给出 Doc 和 Base 的 URL；如果返回里没有 URL，至少给 token 并说明。

## 常用命令索引

- 创建 Base：`lark-cli base +base-create --name "..."`
- 创建子表：`lark-cli base +table-create --base-token <token> --name "..."`
- 批量写记录：`lark-cli base +record-batch-create --base-token <token> --table-id <table> --json @records.json`
- 创建仪表盘：`lark-cli base +dashboard-create --base-token <token> --name "..."`
- 创建图表组件：`lark-cli base +dashboard-block-create --base-token <token> --dashboard-id <id> --name "..." --type column --data-config @config.json`
- 创建报告：`lark-cli docs +create --title "..." --markdown "..."`

详细参数以 `references/` 中对应命令文档为准。
