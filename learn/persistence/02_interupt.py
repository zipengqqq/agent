import sqlite3
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

# --- 1. 定义状态 ---
class State(TypedDict):
    amount: int       # 转账金额
    status: str       # 当前状态

# --- 2. 定义节点 ---

def step_1_prepare(state: State):
    print("🤖 步骤1: AI 正在填写转账单...")
    # AI 决定转账 100 元，状态设为等待批准
    return {"amount": 100, "status": "waiting_approval"}

def step_2_execute(state: State):
    print("✅ 步骤2: 银行接口调用成功！转账完成。")
    return {"status": "success"}

# --- 3. 构建图 ---
workflow = StateGraph(State)
workflow.add_node("prepare", step_1_prepare)
workflow.add_node("execute", step_2_execute)

workflow.add_edge(START, "prepare")
workflow.add_edge("prepare", "execute")
workflow.add_edge("execute", END)

# ==========================================
# 4. 关键设置：打断点
# ==========================================
conn = sqlite3.connect("pause.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

# interrupt_before=["execute"]:
# 意思是：程序运行完 prepare 后，发现下一步是 execute，
# 系统会立马像被定身一样停住，并自动保存当前状态到数据库。
app = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["execute"]
)

# ==========================================
# 5. 运行 (触发中断)
# ==========================================
config = {"configurable": {"thread_id": "user_888"}}

print("--- 🟢 开始运行 ---")
app.invoke({"status": "init"}, config)

print("\n--- ⏸️ 程序已暂停 (你还没看到步骤2被打印) ---")

# ==========================================
# 6. 查房 (Inspect State)
# ==========================================
# 我们来看看它停在哪了
snapshot = app.get_state(config)

print("\n--- 🕵️‍♂️ 侦探模式：查看当前状态 ---")
print(f"当前数据 (Values): {snapshot.values}")
print(f"下一步计划 (Next):   {snapshot.next}")