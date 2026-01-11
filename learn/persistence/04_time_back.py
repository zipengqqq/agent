import sqlite3
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from pathlib import Path

if Path('time_travel.db').exists():
    Path('time_travel.db').unlink()

# --- 1. 定义图结构 (保持和之前一样) ---
class State(TypedDict):
    amount: int
    status: str

def step_1_prepare(state: State):
    return {"amount": 100, "status": "waiting"}

def step_2_execute(state: State):
    # 我们观察这里打印的是 100 还是 9999
    print(f"✅ 步骤2: 执行转账! 金额: {state['amount']}")
    return {"status": "success"}

workflow = StateGraph(State)
workflow.add_node("prepare", step_1_prepare)
workflow.add_node("execute", step_2_execute)
workflow.add_edge(START, "prepare")
workflow.add_edge("prepare", "execute")
workflow.add_edge("execute", END)

conn = sqlite3.connect("time_travel.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)
app = workflow.compile(checkpointer=checkpointer, interrupt_before=["execute"])
config = {"configurable": {"thread_id": "user_999"}}

print("第一次运行，正常暂停")
app.invoke({"status": "init"}, config)

print("修改数据（改成9999）并跑完")
app.update_state(config, {"amount": 9999})
app.invoke(None, config)

"""此时，数据库里最新的状态是9999"""
print("查看历史存档")
history = list(app.get_state_history(config))

# 打印存档
for i, snapshot in enumerate(history):
    amt = snapshot.values.get('amount', 'N/A')
    print(f"[{i}] checkpoint_id: {snapshot.config['configurable']['checkpoint_id']} | 金额: {amt}")

# 寻找目标存档
target_id = None
for snapshot in history:
    if snapshot.values.get("amount") == 100 and snapshot.values.get("status") == "waiting":
        target_id = snapshot.config["configurable"]["checkpoint_id"]
        print(f"已找到目标存档：{target_id}")
        break

# 开始穿越
print(f"发动时光倒流（回到100元的时刻）")
replay_config = {
    "configurable": {
        "thread_id": "user_999",
        "checkpoint_id": target_id
    }
}

# 继续执行
app.invoke(None, replay_config)