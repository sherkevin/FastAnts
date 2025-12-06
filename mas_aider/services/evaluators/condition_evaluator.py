"""
统一条件评估引擎 - 使用 AST 解析表达式

整合了系统条件、Agent决策、状态表达式、复合条件，
并支持通过workflow router热拔插自定义条件逻辑。

使用 Python AST 模块进行表达式解析，确保正确的运算符优先级和括号处理。
"""

import ast
import operator
import re
from typing import Dict, Any, Callable, Optional

# 可选导入：BaseRouter（避免循环依赖）
try:
    from ...core.router_base import BaseRouter
except ImportError:
    BaseRouter = None


# 定义支持的操作符（只允许这些）
ALLOWED_OPERATORS = {
    # 比较
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    # 布尔
    ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b,
    ast.Not: operator.not_,
}


class UnifiedConditionEvaluator:
    """
    统一条件评估引擎 - 使用 AST 解析表达式
    
    支持的条件类型：
    1. 系统条件: "true", "false", "always", "never", "max_turns_exceeded"
    2. Agent决策: 从agent_response.decisions读取的任何字段
    3. 状态表达式: "turn_count > 5", "quality_score >= 8"
    4. 复合条件: "NOT design_confirmed AND NOT ready_to_build"
    5. Workflow特定条件: 通过router注入的自定义逻辑
    
    运算符优先级（由 Python AST 自动处理）：
    1. 小括号 () - 最高优先级
    2. NOT（一元运算符）
    3. 比较运算符 (<, <=, >, >=, ==, !=)
    4. AND
    5. OR - 最低优先级
    """
    
    def __init__(self, max_turns: int = 10, workflow_router: Optional['BaseRouter'] = None):
        """
        初始化统一条件评估器
        
        Args:
            max_turns: 最大轮次限制
            workflow_router: Workflow特定的router（可选）
        """
        self.max_turns = max_turns
        self.workflow_router = workflow_router
        
        # 系统预定义条件（最高优先级）
        # 注意：max_turns_exceeded 和 error_occurred 需要从 system_state 获取
        # 这里暂时保留兼容性，实际应该通过 system_state 参数传递
        self.system_conditions: Dict[str, Callable] = {
            "true": lambda agent_response, state: True,
            "false": lambda agent_response, state: False,
            "always": lambda agent_response, state: True,
            "never": lambda agent_response, state: False,
            # max_turns_exceeded 和 error_occurred 需要从 system_state 获取，这里暂时保留兼容性
            # 实际使用时应该通过 evaluate 方法的 system_state 参数传递
            "max_turns_exceeded": lambda agent_response, state: False,  # 暂时禁用，需要从 system_state 获取
            "error_occurred": lambda agent_response, state: state.get("error") is not None,
        }
    
    def evaluate(self, condition_expr: str, agent_response: Dict[str, Any], condition_state: Dict[str, Any] = None, system_state: Dict[str, Any] = None) -> bool:
        """
        评估条件表达式（支持通用条件和workflow特定条件）
        
        Args:
            condition_expr: 条件表达式
            agent_response: Agent的完整响应（包含decisions）
            condition_state: 条件状态（包含细粒度turn_count等，不包含系统内部状态）
            system_state: 系统内部状态（total_turns, error等，Agent不感知）
            
        Returns:
            bool: 条件是否满足
        """
        if not condition_expr or condition_expr.strip() == "":
            return True
        
        condition_expr = condition_expr.strip()
        condition_state = condition_state or {}
        system_state = system_state or {}
        
        # 1. 系统预定义条件（最高优先级）
        if condition_expr in self.system_conditions:
            # max_turns_exceeded 和 error_occurred 需要从 system_state 获取
            if condition_expr == "max_turns_exceeded":
                total_turns = system_state.get("total_turns", 0)
                return total_turns >= self.max_turns
            elif condition_expr == "error_occurred":
                return system_state.get("error") is not None
            else:
                # 其他系统条件（true, false, always, never）
                return self.system_conditions[condition_expr](agent_response, condition_state)
        
        # 2. Workflow特定条件（通过router注入，在AST解析之前检查）
        if self.workflow_router and self.workflow_router.has_condition(condition_expr):
            try:
                return self.workflow_router.evaluate_condition(
                    condition_expr, agent_response, condition_state, system_state
                )
            except Exception as e:
                print(f"Warning: Failed to evaluate workflow condition '{condition_expr}': {e}")
                # 继续尝试AST解析
        
        # 3. 使用AST解析表达式（支持变量、比较、逻辑运算）
        try:
            # 构建变量查找表（从decisions和condition_state中获取）
            variables = self._build_variable_lookup(agent_response, condition_state)
            
            # 使用AST安全解析和评估
            return self._safe_eval(condition_expr, variables)
        except (ValueError, SyntaxError) as e:
            # AST解析失败，回退到旧逻辑（向后兼容）
            print(f"Warning: AST evaluation failed for '{condition_expr}': {e}, falling back to legacy evaluation")
            return self._legacy_evaluate(condition_expr, agent_response, condition_state)
    
    def _build_variable_lookup(self, agent_response: Dict[str, Any], condition_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建变量查找表
        
        优先级：
        1. agent_response.decisions（Agent决策）- 业务逻辑
        2. condition_state（条件状态）- 细粒度 turn_count 等
        
        Args:
            agent_response: Agent响应
            condition_state: 条件状态（细粒度 turn_count，不包含系统内部状态）
            
        Returns:
            Dict[str, Any]: 变量名到值的映射
        """
        variables = {}
        
        # 从decisions中获取变量（业务决策，最高优先级）
        decisions = agent_response.get("decisions", {})
        for key, value in decisions.items():
            # 转换为Python布尔值或数值
            if isinstance(value, bool):
                variables[key] = value
            elif isinstance(value, (int, float)):
                variables[key] = value
            elif isinstance(value, str):
                # 字符串转布尔："true"/"True" -> True, "false"/"False" -> False
                if value.lower() in ("true", "1", "yes"):
                    variables[key] = True
                elif value.lower() in ("false", "0", "no"):
                    variables[key] = False
                else:
                    variables[key] = value  # 保留字符串值
            else:
                variables[key] = bool(value)  # 其他类型转布尔
        
        # 从condition_state中获取变量（细粒度 turn_count 等，decisions优先）
        for key, value in condition_state.items():
            if key not in variables:  # 不覆盖decisions中的值
                if isinstance(value, (bool, int, float, str)):
                    variables[key] = value
                else:
                    variables[key] = bool(value)
        
        return variables
    
    def _normalize_expression(self, expr: str) -> str:
        """
        将表达式转换为 Python 语法
        
        将 NOT -> not, AND -> and, OR -> or
        
        Args:
            expr: 原始表达式
            
        Returns:
            str: Python 语法表达式
        """
        # 使用正则表达式替换，但要避免替换变量名中的关键字
        # 例如：NOT design_confirmed -> not design_confirmed
        # 但要注意：NOT (A AND B) -> not (A and B)
        
        # 先替换运算符，使用单词边界确保不会误替换
        # NOT 作为一元运算符，后面跟空格或括号
        expr = re.sub(r'\bNOT\b', 'not', expr, flags=re.IGNORECASE)
        # AND 和 OR 作为二元运算符，前后都有空格或括号
        expr = re.sub(r'\bAND\b', 'and', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bOR\b', 'or', expr, flags=re.IGNORECASE)
        
        return expr
    
    def _safe_eval(self, expr: str, variables: Dict[str, Any]) -> bool:
        """
        安全地计算一个只包含基本字面量和指定运算符的表达式。
        
        支持: True, False, 数字, 字符串, (), NOT, AND, OR, ==, !=, <, <=, >, >=
        
        Args:
            expr: 表达式字符串
            variables: 变量查找表
            
        Returns:
            bool: 表达式结果
        """
        try:
            # 先将表达式转换为 Python 语法
            python_expr = self._normalize_expression(expr)
            
            # 解析表达式为AST
            tree = ast.parse(python_expr, mode='eval')
            return self._eval_node(tree.body, variables)
        except Exception as e:
            raise ValueError(f"Invalid expression: {expr}") from e
    
    def _eval_node(self, node: ast.AST, variables: Dict[str, Any]) -> Any:
        """
        递归评估AST节点
        
        Args:
            node: AST节点
            variables: 变量查找表
            
        Returns:
            节点的值
        """
        # 常量（True, False, 数字, 字符串）
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif hasattr(ast, 'Num') and isinstance(node, ast.Num):  # Python < 3.8 兼容
            return node.n
        elif hasattr(ast, 'Str') and isinstance(node, ast.Str):  # Python < 3.8 兼容
            return node.s
        elif hasattr(ast, 'NameConstant') and isinstance(node, ast.NameConstant):  # Python < 3.8 兼容 (True, False, None)
            return node.value
        
        # 变量名（从variables中查找）
        elif isinstance(node, ast.Name):
            var_name = node.id
            if var_name in variables:
                return variables[var_name]
            elif var_name in ('True', 'False', 'None'):
                return eval(var_name)  # 安全的字面量
            else:
                raise ValueError(f"Undefined variable: {var_name}")
        
        # 布尔运算 (AND / OR)
        elif isinstance(node, ast.BoolOp):
            values = [self._eval_node(v, variables) for v in node.values]
            op = ALLOWED_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported boolean operator: {type(node.op)}")
            
            # 链式运算：a AND b AND c
            result = values[0]
            for v in values[1:]:
                result = op(result, v)
            return result
        
        # 一元运算 (NOT)
        elif isinstance(node, ast.UnaryOp):
            op = ALLOWED_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
            return op(self._eval_node(node.operand, variables))
        
        # 比较运算 (==, !=, <, <=, >, >=)
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, variables)
            # 支持链式比较：a < b < c
            for op, right_node in zip(node.ops, node.comparators):
                right = self._eval_node(right_node, variables)
                cmp_op = ALLOWED_OPERATORS.get(type(op))
                if cmp_op is None:
                    raise ValueError(f"Unsupported comparison operator: {type(op)}")
                if not cmp_op(left, right):
                    return False
                left = right  # 链式比较的中间值
            return True
        
        # 表达式包装
        elif isinstance(node, ast.Expression):
            return self._eval_node(node.body, variables)
        
        else:
            raise ValueError(f"Disallowed AST node: {type(node)}")
    
    def _legacy_evaluate(self, condition_expr: str, agent_response: Dict[str, Any], condition_state: Dict[str, Any]) -> bool:
        """
        旧版评估逻辑（向后兼容）
        
        当AST解析失败时，使用此方法作为fallback
        """
        # Agent决策条件 (从decisions字段读取)
        decisions = agent_response.get("decisions", {})
        if condition_expr in decisions:
            return bool(decisions[condition_expr])
        
        # 状态表达式条件 (turn_count_client_supplier_clarify > 5)
        if self._is_state_expression(condition_expr):
            return self._evaluate_state_expression(condition_expr, condition_state)
        
        # 默认处理 - 尝试从条件状态获取
        return bool(condition_state.get(condition_expr, False))
    
    def _is_state_expression(self, expr: str) -> bool:
        """检查是否是状态表达式 (包含比较运算符)"""
        return any(op in expr for op in [">=", "<=", "!=", "==", ">", "<", "="])
    
    def _evaluate_state_expression(self, expr: str, state: Dict[str, Any]) -> bool:
        """评估状态表达式（旧版实现，作为fallback）"""
        try:
            # 先提取运算符，避免替换复合运算符（>=, <=, !=）中的等号
            if ">=" in expr or "<=" in expr or "!=" in expr:
                pass
            elif "=" in expr and "==" not in expr:
                expr = expr.replace("=", "==")
            
            # 提取变量名和值
            var_match = re.match(r'(\w+)\s*([><=!]+)\s*(.+)', expr)
            if var_match:
                var_name, op, value_str = var_match.groups()
                var_value = state.get(var_name)
                if var_value is None:
                    return False
                
                # 转换比较值
                try:
                    if "." in value_str or "e" in value_str.lower():
                        compare_value = float(value_str)
                    else:
                        compare_value = int(value_str)
                except ValueError:
                    compare_value = value_str.strip('"\'')
                
                # 执行比较
                if op == "==":
                    return var_value == compare_value
                elif op == "!=":
                    return var_value != compare_value
                elif op == ">":
                    return var_value > compare_value
                elif op == ">=":
                    return var_value >= compare_value
                elif op == "<":
                    return var_value < compare_value
                elif op == "<=":
                    return var_value <= compare_value
            
            return False
        except Exception as e:
            print(f"Warning: Failed to evaluate expression '{expr}': {e}")
            return False
