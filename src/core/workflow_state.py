"""
Workflow State Schema - LangGraph状态定义

定义LangGraph使用的工作流状态结构。
"""

from typing import TypedDict, Optional, List, Dict, Any
from langchain_core.messages import BaseMessage


class WorkflowState(TypedDict, total=False):
    """
    LangGraph工作流状态
    
    包含Agent通信、执行状态、全局信息等所有必要字段。
    使用total=False允许部分字段为可选。
    """
    
    # ============ Agent通信 ============
    messages: List[BaseMessage]
    """Agent间的消息历史（LangChain格式）"""
    
    # ============ 最新Agent执行信息 ============
    last_agent: str
    """最后执行的Agent名称"""
    
    last_content: str
    """最后一次Agent响应的内容"""
    
    decisions: Dict[str, Any]
    """最新的Agent决策结果（从Agent响应解析）"""
    
    # ============ 系统内部状态（Agent不感知）============
    total_turns: int
    """总交互次数（用于 max_turns 检查）"""
    
    # ============ 细粒度 turn_count（Agent可感知，用于 condition）============
    # 动态字段：turn_count_{agent}_{state}
    # 例如：turn_count_client_supplier_clarify = 2
    
    execution_history: List[Dict[str, Any]]
    """
    执行历史记录
    每个元素包含: {
        "state": str,           # 状态名
        "agent": str,           # Agent名
        "decisions": dict,      # 决策结果
        "turn_count": int       # 轮次
    }
    """
    
    workspace_info: Dict[str, Any]
    """
    工作区信息
    包含: {
        "base_dir": Path,
        "workflow_dir": Path,
        "collab_dir": Path,
        "agent_dirs": dict
    }
    """
    
    initial_message: str
    """工作流初始任务目标"""
    
    workflow_name: str
    """工作流名称"""
    
    # ============ 错误追踪 ============
    error: Optional[str]
    """错误信息（如果有）"""
    
    error_state: Optional[str]
    """发生错误的状态名称"""
    
    # ============ 其他元数据 ============
    start_time: Optional[float]
    """工作流开始时间（时间戳）"""
    
    agent_responses: Optional[List[Dict[str, Any]]]
    """
    所有Agent响应的完整记录（可选）
    每个元素包含: {
        "state": str,
        "agent": str,
        "response": dict,
        "timestamp": float
    }
    """


def create_initial_state(
    workflow_name: str,
    initial_message: str,
    workspace_info: Dict[str, Any]
) -> WorkflowState:
    """
    创建初始工作流状态
    
    Args:
        workflow_name: 工作流名称
        initial_message: 初始任务目标
        workspace_info: 工作区信息
        
    Returns:
        WorkflowState: 初始化的状态对象
    """
    import time
    
    return WorkflowState(
        messages=[],
        last_agent="",
        last_content="",
        decisions={},
        total_turns=0,  # 总交互次数（系统内部）
        execution_history=[],
        workspace_info=workspace_info,
        initial_message=initial_message,
        workflow_name=workflow_name,
        error=None,
        error_state=None,
        start_time=time.time(),
        agent_responses=[]
    )


def extract_agent_context(state: WorkflowState) -> Dict[str, Any]:
    """
    从LangGraph State中提取Agent执行所需的上下文
    
    Args:
        state: 当前工作流状态
        
    Returns:
        Dict: Agent上下文信息，包含：
            - agent_response: Agent响应（decisions）
            - condition_state: 条件状态（细粒度 turn_count，Agent可感知）
            - system_state: 系统内部状态（total_turns, error等，Agent不感知）
    """
    # 提取细粒度 turn_count（格式：turn_count_{agent}_{state}）
    condition_state = {}
    for key, value in state.items():
        if key.startswith("turn_count_"):
            condition_state[key] = value
    
    # 系统内部状态（Agent不感知）
    system_state = {
        "total_turns": state.get("total_turns", 0),
        "error": state.get("error"),
        "execution_history": state.get("execution_history", []),
        "workflow_name": state.get("workflow_name", ""),
        "initial_message": state.get("initial_message", ""),
    }
    
    return {
        "agent_response": {
            "content": state.get("last_content", ""),
            "decisions": state.get("decisions", {})
        },
        "condition_state": condition_state,
        "system_state": system_state
    }
