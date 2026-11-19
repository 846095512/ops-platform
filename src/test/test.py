import sys
import traceback
from loguru import logger


# ================== 核心诊断代码开始 ==================
def diagnose_sinks(stage: str):
    print(f"\n[DIAG] ===== 阶段: {stage} =====")
    print(f"[DIAG] 当前已挂载 sink 数量: {len(logger._core.handlers)}")
    for hid, handler in logger._core.handlers.items():
        # 安全获取级别名称
        level_name = getattr(handler, 'level_name', f"UNKNOWN(level_no={getattr(handler, 'level_no', '?')})")

        # 安全获取 sink 类型 (兼容不同 loguru 版本)
        sink_obj = getattr(handler, 'sink', None) or getattr(handler, '_sink', None)
        sink_type = type(sink_obj).__name__ if sink_obj else "UNKNOWN"

        print(f"[DIAG]   -> Sink ID: {hid} | 级别: {level_name} | 目标类型: {sink_type}")


# 1. 检查进入 setup_logging 时的状态
diagnose_sinks("setup_logging 刚进入")

# 2. 打印当前的调用栈，看看是谁触发了 setup_logging
print("\n[DIAG] 当前调用栈 (谁调用了 setup_logging?):")
traceback.print_stack()

# 3. 动态拦截 logger.add 和 logger.remove，监控谁在修改 sink
original_add = logger.add
original_remove = logger.remove


def traced_add(*args, **kwargs):
    print(f"\n[DIAG] ⚠️ 检测到 logger.add 被调用! 参数: {kwargs.get('level', '默认')}")
    traceback.print_stack()  # 打印是谁调用了 add
    return original_add(*args, **kwargs)


def traced_remove(*args, **kwargs):
    print(f"\n[DIAG] ⚠️ 检测到 logger.remove 被调用! 参数: {args}")
    traceback.print_stack()  # 打印是谁调用了 remove
    return original_remove(*args, **kwargs)


logger.add = traced_add
logger.remove = traced_remove
# ================== 核心诊断代码结束 ==================