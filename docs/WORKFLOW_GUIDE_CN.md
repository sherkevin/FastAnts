# Weaver 工作流工程指南

本文档提供了在 Weaver 中设计、编写和优化工作流的详细指南。`workflow.yaml` 文件是多智能体系统的大脑，它定义了智能体、它们的角色以及控制它们交互的逻辑。

## 📋 目录

1. [工作流结构](#1-工作流结构)
2. [元数据](#2-元数据)
3. [智能体定义](#3-智能体定义)
4. [状态机（核心）](#4-状态机核心)
5. [编写 Prompt](#5-编写-prompt)
6. [条件逻辑](#6-条件逻辑)
7. [退出条件](#7-退出条件)
8. [最佳实践](#8-最佳实践)

---

## 1. 工作流结构

一个有效的 `workflow.yaml` 包含四个主要部分：

```yaml
# 1. 元数据
name: "workflow_name"
description: "人类可读的描述"
initial_message: "初始任务或目标"
max_turns: 10

# 2. 智能体
agents:
  - name: "agent_name"
    type: "coder"  # 或 "architect", "ask"

# 3. 状态（图节点）
states:
  - name: "state_name"
    agent: "agent_name"
    start: true
    prompt: |
      ...
    transitions:
      - to: "next_state"
        condition: "condition_expression"

# 4. 退出条件（可选）
exit_conditions:
  - condition: "max_turns_exceeded"
    action: "force_end"
```

---

## 2. 元数据

定义工作流身份和边界的全局设置。

| 字段 | 类型 | 必需 | 描述 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| `name` | `string` | ✅ 是 | 工作流的唯一标识符。必须与文件夹名称匹配。 | `hulatang` |
| `description` | `string` | ❌ 否 | 人类可读的描述，说明工作流的功能。 | `PPT制作工作流` |
| `initial_message` | `string` | ✅ 是 | 传递给第一个智能体的全局目标或初始指令。 | `制作一份宣传PPT` |
| `max_turns` | `int` | ✅ 是 | 防止无限循环的安全限制。默认值：10 | `20` |

**示例：**
```yaml
name: "hulatang"
description: "胡辣汤宣传PPT制作工作流：自然对话协作，生成HTML PPT"
initial_message: "制作一份关于胡辣汤的宣传PPT"
max_turns: 10
```

---

## 3. 智能体定义

定义此工作流中可用的"角色阵容"。

```yaml
agents:
  - name: "client"        # 在 'states' 中使用的 ID
    type: "coder"         # 标准编码器（快速编码）
  - name: "architect"     # 在 'states' 中使用的 ID
    type: "architect"     # 架构师编码器（高推理能力）
  - name: "reviewer"      # 在 'states' 中使用的 ID
    type: "ask"           # 询问编码器（问题导向）
```

### 智能体类型

| 类型 | 描述 | 使用场景 |
| :--- | :--- | :--- |
| `coder` | 标准 Aider Coder | 快速代码生成和编辑。最适合实现任务。 |
| `architect` | Architect Coder | 高推理能力。最适合设计和架构决策。 |
| `ask` | Ask Coder | 问题导向。最适合澄清和需求收集。 |

**注意：** 每个智能体都有自己的工作空间目录，并可以访问共享的 `collab/` 目录。

---

## 4. 状态机（核心）

`states` 部分定义了 LangGraph 的节点。每个状态代表特定智能体采取行动的一个回合。

### 状态结构

```yaml
states:
  - name: "design_phase"      # 此状态的唯一 ID
    agent: "architect"        # 在此状态下行动的智能体
    start: true               # 标记为入口点（只能有一个状态为 true）
    
    # 此状态的系统提示词
    prompt: |
      【system prompt】：{{COLLABORATION_GUIDE}}
      【role】：你是架构师。
      【任务目标】：{{initial_message}}
      
      审查 {{last_agent_name}} 提交的代码。
      上一轮回复：{{last_agent_content}}
      
      {% if last_agent_name == "developer" %}
      开发者已提交代码。请审查。
      {% else %}
      这是初始设计阶段。
      {% endif %}
      
      【decisions字段说明】：
      {
        "decisions": {
          "approved": true  // boolean: true 表示设计已批准
        }
      }
    
    # 状态流转
    transitions:
      - to: "coding_phase"
        condition: "approved"
      - to: "design_phase"
        condition: "NOT approved"
      - to: "END"
        condition: "approved AND max_turns_exceeded"
```

### 状态字段

| 字段 | 类型 | 必需 | 描述 |
| :--- | :--- | :--- | :--- |
| `name` | `string` | ✅ 是 | 此状态的唯一标识符 |
| `agent` | `string` | ✅ 是 | 在此状态下行动的智能体名称（必须在 `agents` 中定义） |
| `start` | `boolean` | ❌ 否 | 标记为入口点。只有一个状态应该有 `start: true` |
| `prompt` | `string` | ✅ 是 | 此状态的提示词模板（支持模板变量） |
| `transitions` | `array` | ❌ 否 | 转移到其他状态的列表。如果为空，默认转到 END |

---

## 5. 编写 Prompt

Prompt 是你对智能体行为进行编程的地方。Weaver 使用模板变量替换和条件逻辑来实现动态 Prompt。

### 可用模板变量

| 变量 | 描述 | 示例 |
| :--- | :--- | :--- |
| `{{initial_message}}` | 元数据中定义的全局目标 | `"制作一份宣传PPT"` |
| `{{last_agent_name}}` | 上一个行动的智能体名称 | `"client"` |
| `{{last_agent_content}}` | 上一个智能体的文本回复内容 | `"我已经创建了需求文档..."` |
| `{{last_agent_decisions}}` | 上一个智能体的决策对象 | `{"approved": true}` |
| `{{COLLABORATION_GUIDE}}` | 标准协作指南（务必包含！） | 参见 `src/workflows/guide.py` |
| `{{turn_count}}` | 总轮次数（已废弃，使用具体的轮次计数） | `5` |

### Prompt 中的条件逻辑

Weaver 支持使用类似 Jinja2 的语法进行条件块：

```yaml
prompt: |
  {% if last_agent_name == "supplier" %}
  供应商已回复。请审查他们的提案。
  {% else %}
  这是初始请求。请创建需求文档。
  {% endif %}
```

**支持的条件语法：**
- `{% if last_agent_name == "agent_name" %}...{% else %}...{% endif %}`
- 仅支持与 `last_agent_name` 的相等比较

### "文件优先，JSON 在后" 规则

为了确保系统可靠运行，你**必须**强制执行严格的输出格式。**务必在 Prompt 中包含 `{{COLLABORATION_GUIDE}}`。**

智能体的输出**必须**遵循此顺序：
1. **文件操作**：创建文件、编写代码、Diff。所有交付物放在 `collab/` 目录下。
2. **JSON 控制块**：位于最后的一个 JSON 对象，包含 `content` 和 `decisions`。

**Prompt 示例：**
```yaml
prompt: |
  【system prompt】：{{COLLABORATION_GUIDE}}
  【role】：你是架构师。
  【任务目标】：{{initial_message}}
  
  审查 {{last_agent_name}} 提交的代码。
  上一轮回复：{{last_agent_content}}
  
  请审查代码并提供反馈。
  
  【decisions字段说明】：
  {
    "content": "审查意见和变更总结",
    "decisions": {
      "approved": true,        // boolean: true 表示代码已批准
      "needs_revision": false  // boolean: true 表示需要修订
    }
  }
```

**重要提示：**
- 始终在开头包含 `{{COLLABORATION_GUIDE}}`
- JSON 块必须在最后
- `decisions` 对象是必需的，用于评估转移条件
- 所有共享交付物必须放在 `collab/` 目录下

---

## 6. 条件逻辑

Transitions 决定了工作流的下一步去向。Weaver 使用简单的表达式评估器，针对智能体 JSON 响应返回的 `decisions` 对象评估条件。

### 逻辑源

条件是针对智能体 JSON 响应返回的 `decisions` 对象进行评估的。

**智能体响应：**
```json
{
  "content": "我已经完成任务...",
  "decisions": {
    "is_finished": true,
    "has_errors": false,
    "satisfaction_score": 8
  }
}
```

**工作流流转：**
```yaml
transitions:
  - to: "end_state"
    condition: "is_finished AND NOT has_errors"
  - to: "retry_state"
    condition: "has_errors OR satisfaction_score < 7"
  - to: "END"
    condition: "is_finished AND satisfaction_score >= 8"
```

### 支持的操作符

| 操作符 | 描述 | 示例 |
| :--- | :--- | :--- |
| `AND` | 逻辑与 | `approved AND ready_to_build` |
| `OR` | 逻辑或 | `has_errors OR needs_revision` |
| `NOT` | 逻辑非 | `NOT approved` |
| `==` | 相等 | `status == "complete"` |
| `!=` | 不等 | `status != "error"` |
| `>`, `<` | 比较 | `score > 8`, `turns < 5` |
| `>=`, `<=` | 比较 | `score >= 8`, `turns <= 10` |
| `()` | 分组 | `(A AND B) OR C` |

### 特殊条件

- `"END"` - 特殊目标，终止工作流
- 条件按顺序评估，第一个匹配的生效
- 如果没有条件匹配，工作流结束

**示例：**
```yaml
transitions:
  - to: "supplier_create"
    condition: "design_confirmed AND ready_to_build"
  - to: "client_discuss"
    condition: "NOT (design_confirmed AND ready_to_build)"
  - to: "END"
    condition: "approved OR satisfaction_score >= 8"
```

---

## 7. 退出条件

全局退出条件，无论状态转移如何，都可以终止工作流。

```yaml
exit_conditions:
  - condition: "max_turns_exceeded"
    action: "force_end"
  - condition: "error_occurred"
    action: "save_and_end"
```

### 内置退出条件

| 条件 | 描述 | 触发时机 |
| :--- | :--- | :--- |
| `max_turns_exceeded` | 达到最大轮次 | 当 `total_turns >= max_turns` 时 |
| `error_occurred` | 执行错误 | 当发生未处理的错误时 |

### 退出操作

| 操作 | 描述 |
| :--- | :--- |
| `force_end` | 立即终止工作流 |
| `save_and_end` | 保存当前状态并终止 |

**注意：** 退出条件在评估状态转移之前检查。

---

## 8. 最佳实践

### 1. 保持 Prompt 简洁和专注

- 将通用指令移至 `guide.py` 并使用 `{{COLLABORATION_GUIDE}}`
- 保持 YAML 中的 Prompt 专注于该状态的特定业务逻辑
- 使用条件块处理不同场景

```yaml
prompt: |
  {{COLLABORATION_GUIDE}}
  
  【role】：你是开发者。
  【任务目标】：{{initial_message}}
  
  {% if last_agent_name == "architect" %}
  架构师已批准设计。请实现它。
  {% else %}
  请等待设计批准。
  {% endif %}
```

### 2. 显式决策字段

- 强制智能体在 JSON `decisions` 块中输出布尔标志
- 使用描述性字段名：`approved`, `ready_to_build`, `needs_revision`
- 不要依赖解析自然语言

```yaml
{
  "decisions": {
    "task_complete": true,      // 清晰的布尔标志
    "quality_score": 8,         // 用于条件的数值评分
    "needs_revision": false     // 显式的修订标志
  }
}
```

### 3. 循环安全和错误处理

- 始终为"失败"或"重试"情况设置转移
- 使用 `NOT` 条件处理负面情况
- 设置适当的 `max_turns` 以防止无限循环

```yaml
transitions:
  - to: "next_state"
    condition: "approved"
  - to: "current_state"  # 失败时重试
    condition: "NOT approved"
  - to: "END"            # 安全退出
    condition: "max_turns_exceeded"
```

### 4. Collab 目录约定

- 指示智能体将所有共享交付物放在 `collab/` 目录下
- 私有文件可以放在智能体特定目录中
- 这确保其他智能体可以轻松找到共享资源

### 5. 状态命名约定

- 使用描述性名称：`client_request`, `supplier_discuss`, `architect_review`
- 遵循模式：`{agent}_{action}` 或 `{phase}_{role}`
- 在整个工作流中保持名称一致

### 6. 测试你的工作流

- 从简单的工作流开始（2-3 个状态）
- 测试每个转移路径
- 验证 JSON 解析和条件评估
- 检查退出条件是否正常工作

### 7. 文档化

- 在 YAML 中添加注释说明复杂逻辑
- 记录决策字段及其含义
- 在描述中解释工作流流程

```yaml
# 状态1：甲方提出需求（自然对话）
- name: "client_request"
  agent: "client"
  start: true
  prompt: |
    # ... 带有清晰指令的 prompt
```

---

## 示例：完整工作流

参见 `src/workflows/hulatang/workflow.yaml` 查看生产就绪的完整工作流示例。

---

## 需要帮助？

- 查看 `src/workflows/` 中的现有工作流
- 查看 `src/workflows/guide.py` 中的协作指南
- 查看 `src/engines/langgraph_engine.py` 中的 LangGraph 引擎实现
