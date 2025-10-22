import asyncio
from collections import defaultdict

class EventBus:
    def __init__(self):
        self._handlers = defaultdict(list)

    def on(self, event_name, handler):
        """订阅事件"""
        self._handlers[event_name].append(handler)

    def off(self, event_name, handler):
        """取消订阅"""
        self._handlers[event_name].remove(handler)

    async def emit(self, event_name, *args, **kwargs):
        """异步触发事件"""
        if event_name not in self._handlers:
            return
        for handler in self._handlers[event_name]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(*args, **kwargs)
                else:
                    handler(*args, **kwargs)
            except Exception as e:
                print(f"[EventBus] 事件 {event_name} 执行错误:", e)


# 创建一个全局事件总线实例（可在任何模块导入）
event_bus = EventBus()