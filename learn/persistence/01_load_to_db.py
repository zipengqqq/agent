import sqlite3
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
# 引入 SQLite 存档员
from langgraph.checkpoint.sqlite import SqliteSaver

# --- 1. 定义状态 (State) ---
class State(TypedDict):
    # messages 是个列表，用 add 模式（自动追加新消息）
    messages: Annotated[list[str], operator.add]

# --- 2. 定义节点 (Node) ---
def chatbot(state: State):
    # 获取用户最后一句说话
    last_message = state["messages"][-1]
    # 简单的逻辑：给用户的话加个前缀
    return {"messages": [f"AI收到: {last_message}"]}

# --- 3. 构建图 (Graph) ---
workflow = StateGraph(State)
workflow.add_node("bot", chatbot)
workflow.add_edge(START, "bot")
workflow.add_edge("bot", END)

# ==========================================
# 4. 关键步骤：连接 SQLite 数据库
# ==========================================
# 这会在当前目录下生成一个名为 "tutorial.db" 的文件
# check_same_thread=False 是 SQLite 在多线程环境下的推荐配置
conn = sqlite3.connect("tutorial.db", check_same_thread=False)

# 创建存档员
checkpointer = SqliteSaver(conn)

# 编译图时，把 checkpointer 传进去
app = workflow.compile(checkpointer=checkpointer)

# ==========================================
# 5. 第一次运行 (Thread ID = "1")
# ==========================================
config = {"configurable": {"thread_id": "1"}}

print("--- 🟢 第一轮对话 (程序启动) ---")
# 用户说：我叫小明
input_data = {"messages": ["你好，我叫小明"]}
for event in app.stream(input_data, config):
    print(event)

print("--- 🔴 第一轮结束 (假设程序关闭) ---")

# ==========================================
# 6. 第二次运行 (Thread ID = "1")
# ==========================================
# 此时假设是第二天打开程序，我们不需要把 "我叫小明" 再传一遍
# 只要 thread_id 还是 "1"，LangGraph 会自动去 tutorial.db 里找记忆

print("\n--- 🟢 第二轮对话 (重新启动) ---")
# 用户直接问：我叫什么？
new_input = {"messages": ["我刚才说我叫什么？"]}

# 我们来看看 AI 的反应。注意：我们没有手动传历史记录！
final_state = app.invoke(new_input, config)

print("AI 的最终记忆库:", final_state["messages"])