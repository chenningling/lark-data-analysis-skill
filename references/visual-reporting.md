# 图文报告与白板可视化

## 目标

飞书云文档报告不能只写文字。报告中的关键发现应配套可视化图表，并且每个图表都能对应到 Base 里的结果表或仪表盘组件。图表必须贴近对应结论，不能集中堆在文档末尾。

## 可实现能力

| 方式 | 适合场景 | 优点 | 限制 |
| --- | --- | --- | --- |
| Base Dashboard | 交互式看板、可筛选、可回到数据源 | 和 Base 数据天然绑定 | 目前文档 Markdown 里没有可靠方式直接嵌入某个已有 dashboard block |
| 文档白板 | 报告内可视化、流程图、饼图、对比图、经营诊断图 | 留在飞书文档里，适合图文报告 | 需要先在目标段落附近创建空白画板，再用 whiteboard 更新内容 |
| 图片插入 | 柱状图、折线图、复杂 Matplotlib/Plotly 图 | 稳定、所见即所得 | 不是可编辑图表；若 `docs +media-insert` 只能插入末尾，需再调整文档结构或在对应段落先插入白板 |

推荐组合：**Base Dashboard 做交互式看板，Doc 白板/图片做报告叙事图表**。两者使用同一批结果表，并在图表标题或图注里写明对应 Base 表和 Dashboard block。

## 白板工作流

1. 创建或更新文档时，在需要可视化的位置插入空白画板。优先在报告初稿 Markdown 中直接把 `<whiteboard type="blank"></whiteboard>` 放在对应关键发现内；追加修订时，用 `docs +update --mode insert_after` 插入到该结论附近，而不是文档末尾：

```bash
lark-cli docs +update \
  --doc <doc_id_or_url> \
  --mode insert_after \
  --selection-with-ellipsis "关键结论片段..." \
  --markdown '<whiteboard type="blank"></whiteboard>'
```

2. 从返回结果的 `data.board_tokens` 取得画板 token。
3. 根据图表类型选择输入：
   - 需要精确控制颜色、坐标、字体、尺寸、连线、图例时：优先飞书白板内置 DSL，再用 `whiteboard-cli` 转成 OpenAPI raw 写入。
   - 饼图、流程图、思维导图、时序图等简单结构：可用 Mermaid，读 `lark-whiteboard-update.md`。
   - 柱状图、折线图、漏斗图、复杂经营诊断图：优先 DSL/raw；如果 `whiteboard-cli` 不可用，改用 PNG 图片插入。
4. 更新画板：

```bash
cat chart.mmd | lark-cli whiteboard +update \
  --whiteboard-token <board_token> \
  --input_format mermaid \
  --source - \
  --overwrite --yes --as user
```

5. 写入后可用 `docs +media-download --type whiteboard --token <board_token>` 下载缩略图检查。

## DSL 优先规则

当本地存在 `whiteboard-cli` 或用户同意通过 `npx @larksuite/whiteboard-cli` 使用转换工具时，优先写飞书白板 DSL：

- 用 `frame` 固定画布和标题区。
- 用 `text` 控制标题、图注、口径说明。
- 用 `rect`、`connector`、`svg` 等节点绘制条形、卡片、流程和标注。
- 统一设置色板、字号、间距和对齐方式。
- 在图表底部写 `对应 Base 表`、`对应看板组件`、`口径`。

如果当前环境没有 `whiteboard-cli`，不要声称已经实现 DSL 精确控制；应明确记录为 Mermaid 或 PNG 兜底。

## 图片兜底工作流

当白板图表不能稳定生成，或当前环境没有 `whiteboard-cli` 且不能安装时：

1. 用本地 Python/JS 根据结果表生成 PNG。
2. 用 `docs +media-insert` 插入文档。
3. 图片 caption 必须包含对应 Base 结果表/看板组件名称。

```bash
lark-cli docs +media-insert \
  --doc <doc_id_or_url> \
  --file ./chart.png \
  --align center \
  --caption "对应 Base 表：05_月度趋势；对应看板组件：月度有效销售额趋势"
```

## 图表选择

| 分析问题 | Base 看板组件 | 文档图表 |
| --- | --- | --- |
| 总体规模与退款 | 指标卡 | KPI 摘要卡、退款占比饼图 |
| 时间趋势 | line / area | 折线图 |
| SKU/地区排名 | bar / column | Top N 条形图 |
| 优惠券结构 | pie / ring | 饼图或环形图 |
| 转化路径 | funnel | 漏斗图 |
| 根因分析 | text + bar | 白板鱼骨图或治理路径图 |

## 必须写入报告的对应关系

每个图表附近写：

- `对应 Base 表：...`
- `对应看板组件：...`
- `口径：...`

如果图表不是直接来自 Base dashboard，而是本地根据同一结果表生成，也要明确说明“同源于 Base 表”。
