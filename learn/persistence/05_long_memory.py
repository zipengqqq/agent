import operator
import uuid
import os
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore


class State(TypedDict):
    messages: Annotated[list[str], operator.add]


def chatbot(state: State, config):
    # 获取当前用户的ID
    user_id = config["configurable"].get("user_id")

    # 命名空间，用来区分用户的记忆区
    namespace = (user_id, "memories")

    last_msg = state['messages'][-1]

    if "我喜欢" in last_msg:
        preference = last_msg.replace("我喜欢", "").strip()
        print(f"喜好：{preference}")

        # 写入store (使用全局变量 in_memory_store)
        in_memory_store.put(namespace, uuid.uuid4().hex, {"data": preference}) # 后面两个参数的含义依次是：记录id，记录内容

        return {"messages": [f"已记录长期记忆：用户喜欢{preference}"]}

    if "吃什么" in last_msg:
        # postgresql支持，向量搜索
        memories = in_memory_store.search(namespace)

        if memories:
            # 获取第一条记忆的内容
            preference = memories[0].value["data"]
            return {"messages": [f"根据长期记忆，我推荐你去吃：{preference}"]}
        else:
            return {"messages": [f"我还不了解你的口味，先告诉我你喜欢吃什么？"]}

    return {"messages": [f"收到：{last_msg}"]}


workflow = StateGraph(State)
workflow.add_node("bot", chatbot)
workflow.add_edge(START, "bot")
workflow.add_edge("bot", END)

# 加载环境变量
load_dotenv()
DB_URI = os.getenv("POSTGRES_URI")

print("正在连接数据库...")

# 1. 打开短期记忆 (Checkpointer) 的连接
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    # 2. 打开长期记忆 (Store) 的连接
    with PostgresStore.from_conn_string(DB_URI) as in_memory_store:
        # --- 初始化建表 ---
        # 第一次运行时需要 setup，建立 checkpoints 和 store 表
        checkpointer.setup()
        in_memory_store.setup()

        # --- 编译图 ---
        app = workflow.compile(checkpointer=checkpointer, store=in_memory_store)

        # --- 开始运行业务逻辑 ---

        # 聊天窗口1对话
        config_1 = {"configurable": {"thread_id": "1", "user_id": "xiaoming"}}
        app.invoke({"messages": ["我喜欢麻辣烫"]}, config_1)
        print("AI: 已将喜好记录到长期记忆中")

        # 聊天窗口2对话
        config_2 = {"configurable": {"thread_id": "2", "user_id": "xiaoming"}}
        final_state = app.invoke({"messages": ["今天晚上吃什么"]}, config_2)

        print(f"AI的回答：{final_state['messages'][-1]}")

