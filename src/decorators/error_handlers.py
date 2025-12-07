"""
错误处理装饰器

提供统一的异常处理机制，避免在业务逻辑中出现try-catch的额外缩进。
"""

from functools import wraps
from ..diagnostics.exceptions import ConfigurationError, WorkflowException, ExecutionError


def config_load_error_handler(func):
    """配置加载错误处理装饰器

    自动捕获配置加载过程中的异常并转换为ConfigurationError，
    避免在主函数中出现try-catch的额外缩进。

    使用示例:
        @classmethod
        @config_load_error_handler
        def load(cls) -> 'AppConfig':
            # 主要逻辑，无try-catch缩进！
            return do_something()
    """
    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        try:
            return func(cls, *args, **kwargs)
        except ConfigurationError:
            # 已是我们自定义的异常，直接重新抛出
            raise
        except Exception as e:
            # 捕获其他异常，转换为ConfigurationError
            config_path = cls._get_config_path()
            raise ConfigurationError(f"Failed to load config from {config_path}: {e}")
    return wrapper


def workflow_execution_error_handler(func):
    """工作流执行错误处理装饰器

    处理工作流执行过程中的异常，转换为WorkflowException。
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except WorkflowException:
            raise
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"❌ Workflow execution failed: {e}")
            raise WorkflowException(f"Workflow execution failed: {e}")
    return wrapper


def agent_operation_error_handler(func):
    """Agent操作错误处理装饰器

    处理Agent执行过程中的异常，提供统一的错误处理。
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ExecutionError:
            raise
        except Exception as e:
            raise ExecutionError(f"Agent operation failed: {e}")
    return wrapper


def langgraph_node_error_handler(func):
    """LangGraph节点错误处理装饰器
    
    捕获异常，记录日志，并更新state中的error字段，而不是抛出异常中断图执行。
    """
    @wraps(func)
    def wrapper(self, state, *args, **kwargs):
        try:
            return func(self, state, *args, **kwargs)
        except Exception as e:
            state_name = state.get("name", "unknown")
            if hasattr(self, 'logger'):
                self.logger.error(f"❌ Error in node execution '{state_name}': {e}")
            
            state["error"] = str(e)
            state["error_state"] = state_name
            return state
    return wrapper


def langgraph_execution_handler(func):
    """LangGraph执行错误处理装饰器
    
    捕获异常并返回标准错误结果字典。
    """
    @wraps(func)
    def wrapper(self, context, initial_state_data=None, *args, **kwargs):
        try:
            return func(self, context, initial_state_data, *args, **kwargs)
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"❌ Workflow execution failed: {e}")
            
            # 构建错误结果
            return {
                "success": False,
                "final_content": "",
                "total_turns": initial_state_data.get("total_turns", 0) if initial_state_data else 0,
                "agents_used": [],
                "metadata": {
                    "error": str(e),
                    "execution_history": initial_state_data.get("execution_history", []) if initial_state_data else []
                }
            }
    return wrapper


def safe_operation(default_return=None, log_error=True):
    """安全操作装饰器
    
    捕获所有异常，记录日志（可选），并返回默认值。
    适用于不应中断主流程的辅助操作（如日志记录、清理、非关键IO）。
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if log_error and hasattr(self, 'logger'):
                    self.logger.warning(f"⚠️  Operation '{func.__name__}' failed: {e}")
                elif log_error:
                    print(f"⚠️  Operation '{func.__name__}' failed: {e}")
                return default_return
        return wrapper
    return decorator

