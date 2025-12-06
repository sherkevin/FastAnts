"""
Router基类 - Workflow特定条件逻辑的抽象基类

提供统一的接口用于定义workflow特定的条件判断逻辑。
所有workflow的router都应继承此类。
"""

from abc import ABC
from typing import Dict, Any, Callable, Optional


class BaseRouter(ABC):
    """
    Workflow Router基类
    
    通过继承此类并定义check_*方法，可以为workflow添加自定义条件逻辑。
    
    示例:
        ```python
        class MyWorkflowRouter(BaseRouter):
            def check_quality_threshold(self, agent_response: Dict, global_state: Dict) -> bool:
                satisfaction = agent_response.get("decisions", {}).get("satisfaction_score", 0)
                return satisfaction >= 8
        ```
        
        在YAML中使用:
        ```yaml
        transitions:
          - to: "next_state"
            condition: "quality_threshold"  # 调用check_quality_threshold
        ```
    """
    
    def __init__(self):
        self._conditions: Dict[str, Callable] = {}
        self._auto_register_conditions()
    
    def _auto_register_conditions(self):
        """
        自动注册所有check_*方法为可用条件
        
        遍历类的所有方法，将以"check_"开头的方法注册为条件。
        条件名称为方法名去掉"check_"前缀。
        """
        for attr_name in dir(self):
            if attr_name.startswith("check_") and callable(getattr(self, attr_name)):
                # 去掉"check_"前缀作为条件名称
                condition_name = attr_name[6:]  # len("check_") == 6
                self._conditions[condition_name] = getattr(self, attr_name)
    
    def evaluate_condition(
        self, 
        condition_name: str, 
        agent_response: Dict[str, Any], 
        condition_state: Dict[str, Any] = None,
        system_state: Dict[str, Any] = None
    ) -> bool:
        """
        评估workflow特定条件
        
        Args:
            condition_name: 条件名称（不含check_前缀）
            agent_response: Agent响应，包含content和decisions
            condition_state: 条件状态（细粒度 turn_count，Agent可感知）
            system_state: 系统内部状态（total_turns, error等，Agent不感知）
            
        Returns:
            bool: 条件是否满足
            
        Raises:
            ValueError: 如果条件不存在
        """
        condition_state = condition_state or {}
        system_state = system_state or {}
        
        if condition_name in self._conditions:
            # 为了向后兼容，将 condition_state 和 system_state 合并传递给 check_* 方法
            # check_* 方法可以使用 get_state 方法访问状态
            combined_state = {**condition_state, **system_state}
            return self._conditions[condition_name](agent_response, combined_state)
        
        raise ValueError(
            f"Unknown condition: '{condition_name}'. "
            f"Available conditions: {self.list_conditions()}"
        )
    
    def list_conditions(self) -> list[str]:
        """
        列出所有可用的条件名称
        
        Returns:
            list[str]: 条件名称列表
        """
        return list(self._conditions.keys())
    
    def has_condition(self, condition_name: str) -> bool:
        """
        检查是否存在指定条件
        
        Args:
            condition_name: 条件名称
            
        Returns:
            bool: 条件是否存在
        """
        return condition_name in self._conditions
    
    # ============ 辅助方法 ============
    
    def get_decision(
        self, 
        agent_response: Dict[str, Any], 
        key: str, 
        default: Any = None
    ) -> Any:
        """
        安全获取Agent决策字段
        
        Args:
            agent_response: Agent响应
            key: 决策字段名
            default: 默认值
            
        Returns:
            决策字段值或默认值
        """
        return agent_response.get("decisions", {}).get(key, default)
    
    def get_state(
        self, 
        global_state: Dict[str, Any], 
        key: str, 
        default: Any = None
    ) -> Any:
        """
        安全获取全局状态字段
        
        Args:
            global_state: 全局状态
            key: 状态字段名
            default: 默认值
            
        Returns:
            状态字段值或默认值
        """
        return global_state.get(key, default)
    
    def get_last_n_states(
        self, 
        global_state: Dict[str, Any], 
        n: int
    ) -> list[Dict]:
        """
        获取最近N个状态的执行历史
        
        Args:
            global_state: 全局状态
            n: 获取的历史数量
            
        Returns:
            list[Dict]: 最近N个状态的历史记录
        """
        history = global_state.get("execution_history", [])
        return history[-n:] if len(history) >= n else history
    
    # ============ 生命周期 Hooks（可选实现） ============
    
    def on_workflow_start(self, config: Dict[str, Any]) -> None:
        """
        Workflow开始时的hook
        
        Args:
            config: Workflow配置
        """
        pass
    
    def on_workflow_end(self, result: Dict[str, Any]) -> None:
        """
        Workflow结束时的hook
        
        Args:
            result: Workflow执行结果
        """
        pass
    
    def on_state_enter(self, state_name: str, context: Dict[str, Any]) -> None:
        """
        进入状态时的hook
        
        Args:
            state_name: 状态名称
            context: 当前上下文
        """
        pass
    
    def on_state_exit(self, state_name: str, result: Dict[str, Any]) -> None:
        """
        退出状态时的hook
        
        Args:
            state_name: 状态名称
            result: 状态执行结果
        """
        pass
