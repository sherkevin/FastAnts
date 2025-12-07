# Weaver Workflow Engineering Guide

This document provides a comprehensive guide to designing, writing, and optimizing workflows in Weaver. The `workflow.yaml` file is the brain of your multi-agent system, defining the agents, their roles, and the logic that governs their interaction.

## 📋 Table of Contents

1. [Workflow Structure](#1-workflow-structure)
2. [Metadata](#2-metadata)
3. [Agent Definition](#3-agent-definition)
4. [State Machine (The Core)](#4-state-machine-the-core)
5. [Writing Prompts](#5-writing-prompts)
6. [Condition Logic](#6-condition-logic)
7. [Exit Conditions](#7-exit-conditions)
8. [Best Practices](#8-best-practices)

---

## 1. Workflow Structure

A valid `workflow.yaml` consists of four main sections:

```yaml
# 1. Metadata
name: "workflow_name"
description: "Human-readable description"
initial_message: "The initial task or goal"
max_turns: 10

# 2. Agents
agents:
  - name: "agent_name"
    type: "coder"  # or "architect", "ask"

# 3. States (The Graph Nodes)
states:
  - name: "state_name"
    agent: "agent_name"
    start: true
    prompt: |
      ...
    transitions:
      - to: "next_state"
        condition: "condition_expression"

# 4. Exit Conditions (Optional)
exit_conditions:
  - condition: "max_turns_exceeded"
    action: "force_end"
```

---

## 2. Metadata

Global settings that define the identity and boundaries of the workflow.

| Field | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `name` | `string` | ✅ Yes | Unique identifier for the workflow. Must match the folder name. | `hulatang` |
| `description` | `string` | ❌ No | Human-readable description of what the workflow does. | `PPT Creation Workflow` |
| `initial_message` | `string` | ✅ Yes | The global goal or initial instruction passed to the first agent. | `Create a promotional PPT` |
| `max_turns` | `int` | ✅ Yes | Safety limit to prevent infinite loops. Default: 10 | `20` |

**Example:**
```yaml
name: "hulatang"
description: "PPT Creation Workflow: Natural Conversation Collaboration"
initial_message: "Create a promotional PPT about Hulatang"
max_turns: 10
```

---

## 3. Agent Definition

Defines the "cast of characters" available in this workflow.

```yaml
agents:
  - name: "client"        # The ID used in 'states'
    type: "coder"         # Standard coder (fast coding)
  - name: "architect"     # The ID used in 'states'
    type: "architect"     # Architect coder (high reasoning)
  - name: "reviewer"      # The ID used in 'states'
    type: "ask"           # Ask coder (question-focused)
```

### Agent Types

| Type | Description | Use Case |
| :--- | :--- | :--- |
| `coder` | Standard Aider Coder | Fast code generation and editing. Best for implementation tasks. |
| `architect` | Architect Coder | High reasoning capability. Best for design and architecture decisions. |
| `ask` | Ask Coder | Question-focused. Best for clarification and requirements gathering. |

**Note:** Each agent gets its own workspace directory and can access the shared `collab/` directory.

---

## 4. State Machine (The Core)

The `states` section defines the nodes of the LangGraph. Each state represents a turn where a specific agent takes action.

### State Structure

```yaml
states:
  - name: "design_phase"      # Unique ID for this state
    agent: "architect"        # Which agent acts in this state
    start: true               # Marks this as the entry point (only one state can be true)
    
    # The System Prompt for this state
    prompt: |
      【system prompt】：{{COLLABORATION_GUIDE}}
      【role】：You are the Architect.
      【task】：{{initial_message}}
      
      Review the code from {{last_agent_name}}.
      Previous response: {{last_agent_content}}
      
      {% if last_agent_name == "developer" %}
      The developer has submitted code. Please review it.
      {% else %}
      This is the initial design phase.
      {% endif %}
      
      【decisions字段说明】：
      {
        "decisions": {
          "approved": true  // boolean: true if design is approved
        }
      }
    
    # Transitions to other states
    transitions:
      - to: "coding_phase"
        condition: "approved"
      - to: "design_phase"
        condition: "NOT approved"
      - to: "END"
        condition: "approved AND max_turns_exceeded"
```

### State Fields

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | `string` | ✅ Yes | Unique identifier for this state |
| `agent` | `string` | ✅ Yes | Name of the agent that acts in this state (must be defined in `agents`) |
| `start` | `boolean` | ❌ No | Mark as entry point. Only one state should have `start: true` |
| `prompt` | `string` | ✅ Yes | The prompt template for this state (supports template variables) |
| `transitions` | `array` | ❌ No | List of transitions to other states. If empty, defaults to END |

---

## 5. Writing Prompts

Prompts are where you program the agent's behavior. Weaver uses template variable substitution and conditional logic for dynamic prompts.

### Available Template Variables

| Variable | Description | Example |
| :--- | :--- | :--- |
| `{{initial_message}}` | The global goal defined in metadata | `"Create a promotional PPT"` |
| `{{last_agent_name}}` | Name of the agent who acted previously | `"client"` |
| `{{last_agent_content}}` | Text content from the previous agent's response | `"I've created the requirements document..."` |
| `{{last_agent_decisions}}` | Decisions object from the previous agent | `{"approved": true}` |
| `{{COLLABORATION_GUIDE}}` | Standard collaboration guidelines (always include this!) | See `src/workflows/guide.py` |
| `{{turn_count}}` | Total number of turns (deprecated, use specific turn counts) | `5` |

### Conditional Logic in Prompts

Weaver supports conditional blocks using Jinja2-like syntax:

```yaml
prompt: |
  {% if last_agent_name == "supplier" %}
  The supplier has responded. Please review their proposal.
  {% else %}
  This is the initial request. Please create a requirements document.
  {% endif %}
```

**Supported condition syntax:**
- `{% if last_agent_name == "agent_name" %}...{% else %}...{% endif %}`
- Only supports equality comparison with `last_agent_name`

### The "Files First, JSON Last" Rule

To ensure the system works reliably, you **must** enforce a strict output format. **Always include `{{COLLABORATION_GUIDE}}` in your prompt.**

The agent's output **must** follow this sequence:
1. **File Operations**: Creating files, writing code, diffs. All deliverables go in `collab/` directory.
2. **JSON Control Block**: A JSON object at the very end containing `content` and `decisions`.

**Example Prompt:**
```yaml
prompt: |
  【system prompt】：{{COLLABORATION_GUIDE}}
  【role】：You are the Architect.
  【task】：{{initial_message}}
  
  Review the code from {{last_agent_name}}.
  Previous response: {{last_agent_content}}
  
  Please review the code and provide feedback.
  
  【decisions字段说明】：
  {
    "content": "Review comments and summary of changes",
    "decisions": {
      "approved": true,        // boolean: true if code is approved
      "needs_revision": false  // boolean: true if revision is needed
    }
  }
```

**Important:**
- Always include `{{COLLABORATION_GUIDE}}` at the beginning
- The JSON block must be at the end
- The `decisions` object is required and evaluated for transitions
- All shared deliverables must be in the `collab/` directory

---

## 6. Condition Logic

Transitions determine where the workflow goes next. Weaver uses a simple expression evaluator that evaluates conditions against the `decisions` object returned by the agent's JSON response.

### Logic Source

Conditions are evaluated against the `decisions` object from the agent's JSON response.

**Agent Response:**
```json
{
  "content": "I've completed the task...",
  "decisions": {
    "is_finished": true,
    "has_errors": false,
    "satisfaction_score": 8
  }
}
```

**Workflow Transition:**
```yaml
transitions:
  - to: "end_state"
    condition: "is_finished AND NOT has_errors"
  - to: "retry_state"
    condition: "has_errors OR satisfaction_score < 7"
  - to: "END"
    condition: "is_finished AND satisfaction_score >= 8"
```

### Supported Operators

| Operator | Description | Example |
| :--- | :--- | :--- |
| `AND` | Logical AND | `approved AND ready_to_build` |
| `OR` | Logical OR | `has_errors OR needs_revision` |
| `NOT` | Logical NOT | `NOT approved` |
| `==` | Equality | `status == "complete"` |
| `!=` | Inequality | `status != "error"` |
| `>`, `<` | Comparison | `score > 8`, `turns < 5` |
| `>=`, `<=` | Comparison | `score >= 8`, `turns <= 10` |
| `()` | Grouping | `(A AND B) OR C` |

### Special Conditions

- `"END"` - Special target that terminates the workflow
- Conditions are evaluated in order, first match wins
- If no condition matches, workflow ends

**Example:**
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

## 7. Exit Conditions

Global exit conditions that can terminate the workflow regardless of state transitions.

```yaml
exit_conditions:
  - condition: "max_turns_exceeded"
    action: "force_end"
  - condition: "error_occurred"
    action: "save_and_end"
```

### Built-in Exit Conditions

| Condition | Description | When Triggered |
| :--- | :--- | :--- |
| `max_turns_exceeded` | Maximum turns reached | When `total_turns >= max_turns` |
| `error_occurred` | Execution error | When an unhandled error occurs |

### Exit Actions

| Action | Description |
| :--- | :--- |
| `force_end` | Immediately terminate the workflow |
| `save_and_end` | Save current state and terminate |

**Note:** Exit conditions are checked before evaluating state transitions.

---

## 8. Best Practices

### 1. Keep Prompts Clean and Focused

- Move generic instructions to `guide.py` and use `{{COLLABORATION_GUIDE}}`
- Keep YAML prompts focused on state-specific business logic
- Use conditional blocks to handle different scenarios

```yaml
prompt: |
  {{COLLABORATION_GUIDE}}
  
  【role】：You are the Developer.
  【task】：{{initial_message}}
  
  {% if last_agent_name == "architect" %}
  The architect has approved the design. Please implement it.
  {% else %}
  Please wait for design approval.
  {% endif %}
```

### 2. Explicit Decision Fields

- Force agents to output boolean flags in the JSON `decisions` block
- Use descriptive field names: `approved`, `ready_to_build`, `needs_revision`
- Don't rely on parsing natural language

```yaml
{
  "decisions": {
    "task_complete": true,      // Clear boolean flag
    "quality_score": 8,         // Numeric score for conditions
    "needs_revision": false     // Explicit revision flag
  }
}
```

### 3. Loop Safety and Error Handling

- Always have transitions for "failure" or "retry" cases
- Use `NOT` conditions to handle negative cases
- Set appropriate `max_turns` to prevent infinite loops

```yaml
transitions:
  - to: "next_state"
    condition: "approved"
  - to: "current_state"  # Retry on failure
    condition: "NOT approved"
  - to: "END"            # Safety exit
    condition: "max_turns_exceeded"
```

### 4. Collab Directory Convention

- Instruct agents to put all shared deliverables in `collab/` directory
- Private files can go in agent-specific directories
- This ensures other agents can easily find shared resources

### 5. State Naming Conventions

- Use descriptive names: `client_request`, `supplier_discuss`, `architect_review`
- Follow a pattern: `{agent}_{action}` or `{phase}_{role}`
- Keep names consistent across the workflow

### 6. Testing Your Workflow

- Start with simple workflows (2-3 states)
- Test each transition path
- Verify JSON parsing and condition evaluation
- Check that exit conditions work correctly

### 7. Documentation

- Add comments in YAML for complex logic
- Document decision fields and their meanings
- Explain the workflow flow in the description

```yaml
# 状态1：甲方提出需求（自然对话）
- name: "client_request"
  agent: "client"
  start: true
  prompt: |
    # ... prompt with clear instructions
```

---

## Example: Complete Workflow

See `src/workflows/hulatang/workflow.yaml` for a complete example of a production-ready workflow.

---

## Need Help?

- Check existing workflows in `src/workflows/`
- Review the collaboration guide in `src/workflows/guide.py`
- See the LangGraph engine implementation in `src/engines/langgraph_engine.py`
