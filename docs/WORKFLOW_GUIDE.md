# FastAnts Workflow Engineering Guide

This document provides a comprehensive guide to designing, writing, and optimizing workflows in FastAnts. The `workflow.yaml` file is the brain of your multi-agent system, defining the agents, their roles, and the logic that governs their interaction.

## 📋 Table of Contents

1.  [Workflow Structure](#1-workflow-structure)
2.  [Metadata](#2-metadata)
3.  [Agent Definition](#3-agent-definition)
4.  [State Machine (The Core)](#4-state-machine-the-core)
5.  [Writing Prompts](#5-writing-prompts)
6.  [Condition Logic](#6-condition-logic)
7.  [Best Practices](#7-best-practices)

---

## 1. Workflow Structure

A valid `workflow.yaml` consists of four main sections:

```yaml
# 1. Metadata
name: "..."
description: "..."
initial_message: "..."
max_turns: 10

# 2. Agents
agents:
  - ...

# 3. States (The Graph)
states:
  - ...

# 4. Exit Conditions
exit_conditions:
  - ...
```

---

## 2. Metadata

Global settings that define the identity and boundaries of the workflow.

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `name` | `string` | Unique identifier for the workflow. Must match the folder name. | `feature_dev` |
| `description` | `string` | Human-readable description of what the workflow does. | `Collaborative feature implementation` |
| `initial_message` | `string` | The global goal or initial instruction passed to the first agent. | `Implement a login page` |
| `max_turns` | `int` | Safety limit to prevent infinite loops. | `20` |

---

## 3. Agent Definition

Defines the "cast of characters" available in this workflow.

```yaml
agents:
  - name: "architect"    # The ID used in 'states'
    type: "architect"    # Uses Aider's ArchitectCoder (high reasoning)
  - name: "developer"    # The ID used in 'states'
    type: "coder"        # Uses Aider's standard Coder (high coding speed)
```

*   **`type`**: Currently supports `coder` (standard) and `architect` (reasoning-focused).

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
      ...
      
    # Transitions to other states
    transitions:
      - to: "coding_phase"
        condition: "design_approved"
      - to: "design_phase"
        condition: "NOT design_approved"
```

---

## 5. Writing Prompts

Prompts are where you program the agent's behavior. FastAnts uses **Jinja2** templating for dynamic prompts.

### Available Variables

*   `{{initial_message}}`: The global goal defined in metadata.
*   `{{last_agent_content}}`: The text response from the previous agent.
*   `{{last_agent_name}}`: The name of the agent who acted previously.
*   `{{COLLABORATION_GUIDE}}`: The standard guide from `src/workflows/guide.py`.

### The "Files First, JSON Last" Rule

To ensure the system works reliably, you must enforce a strict output format. **Always include `{{COLLABORATION_GUIDE}}` in your prompt.**

The agent's output **must** follow this sequence:
1.  **File Operations**: Creating files, writing code, diffs.
2.  **JSON Control Block**: A JSON object at the very end containing decisions.

**Example Prompt:**
```yaml
    prompt: |
      You are the Architect.
      Goal: {{initial_message}}
      
      Review the code from {{last_agent_name}}.
      
      {{COLLABORATION_GUIDE}}
      
      Reply format (Strict JSON):
      {
        "content": "Review comments...",
        "decisions": {
          "approved": true
        }
      }
```

---

## 6. Condition Logic

Transitions determine where the workflow goes next. FastAnts uses a simple expression evaluator.

### Logic Source
The conditions are evaluated against the `decisions` object returned by the Agent's JSON response.

**Agent Response:**
```json
{
  "decisions": {
    "is_finished": true,
    "has_errors": false
  }
}
```

**Workflow Transition:**
```yaml
    transitions:
      - to: "end_state"
        condition: "is_finished AND NOT has_errors"
```

### Supported Operators
*   `AND`, `OR`, `NOT`
*   `==`, `!=`, `>`, `<`, `>=`, `<=`
*   Parentheses `()` for grouping

---

## 7. Best Practices

1.  **Keep Prompts Clean**: Move generic instructions to `guide.py` and use `{{COLLABORATION_GUIDE}}`. Keep the YAML prompt focused on the specific business logic of that state.
2.  **Explicit Decisions**: Force the agent to output boolean flags (e.g., `approved: true`) in the JSON `decisions` block. Do not rely on parsing natural language.
3.  **Loop Safety**: Always have a transition that handles the "failure" or "retry" case (e.g., `condition: "NOT approved"`), otherwise the graph might end prematurely.
4.  **Collab Directory**: Instruct agents to put all shared deliverables in the `collab/` directory so other agents can easily find them.
