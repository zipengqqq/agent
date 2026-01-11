import sqlite3
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

class State(TypedDict):
    amount: int
    status: str

def step_1_prepare(state: State):
    print(f"🤖步骤1：AI正在准备....")
    return {"amount": 100, "status": "waiting"}

def step2_execute(state: State):
    print(f"✅步骤2：执行转账！金额：{state['amount']}")
    return {"status": "success"}

workflow = StateGraph(State)
workflow.add_node("prepare", step_1_prepare)
workflow.add_node("execute", step2_execute)
workflow.add_edge(START, "prepare")
workflow.add_edge("prepare", "execute")
workflow.add_edge("execute", END)

conn = sqlite3.connect("pause.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

app = workflow.compile(checkpointer=checkpointer, interrupt_before=["execute"])

# 修改前的数据
config = {"configurable": {"thread_id": "user_888"}}
snapshot = app.get_state(config)
print(f"修改前的数据为：{snapshot.values}")

# 执行修改
print(f"正在修改数据")
app.update_state(config, {"amount": 9999})

# 继续执行
print(f"⏩恢复运行")

# 此处传None，告诉程序，不需要新指令，继续执行刚才没有做完的任务
app.invoke(None, config)

# 输出修改后的数据
snapshot = app.get_state(config)
print(f"修改后的数据为：{snapshot.values}")