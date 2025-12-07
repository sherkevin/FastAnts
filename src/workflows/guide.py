"""
协作规范常量
通用协作指南，用于嵌入到Agent prompt中，确保输出格式和协作规范
"""

COLLABORATION_GUIDE = """
## 🛠️ 协作与输出规范 (Collaboration & Output Standards)

### 1. 文件操作规范 (File Operations)
- **交付物 (Deliverables)**：所有最终产出（代码、文档、HTML等）必须写入 `collab/` 目录。
- **操作优先 (Action First)**：**必须**先执行所有的文件创建、修改或读取操作。
- **完整路径 (Full Path)**：引用文件时始终使用完整路径（例如 `collab/design.md`）。

### 2. 交流与反馈 (Communication)
- **自然对话**：使用自然、专业的语言与协作者沟通。
- **明确意图**：清晰表达你的决策、建议或问题。

### 3. 严格输出格式 (Strict Output Format)
你必须严格遵守以下输出顺序，以确保系统正确解析：

1.  **第一步：文件操作与思考**
    - 在这里进行所有的代码编写、文件修改和思考过程。
    - 使用 Aider 的标准格式操作文件。
    - **不要**在这里输出 JSON。

2.  **第二步：控制信号 (Control Signal)**
    - 在回复的**最后**，必须输出一个严格的 JSON 块。
    - 该 JSON 块用于驱动工作流状态机。
    - **严禁**在 JSON 块之后再输出任何内容。

**JSON 格式模板**：
```json
{
  "content": "简要描述你做了什么（例如：'已完成设计文档' 或 '已修复 Bug'）",
  "decisions": {
    "key_decision_1": true,
    "key_decision_2": false
    // 根据当前状态的要求填充决策字段
  }
}
```
"""

# 导出常量供模板使用
__all__ = ["COLLABORATION_GUIDE"]