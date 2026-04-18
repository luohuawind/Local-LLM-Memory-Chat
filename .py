# -*- coding: utf-8 -*-
import os
import json
import requests
from datetime import datetime

# ===================== 核心配置（确认这2项即可） =====================
MEMORY_FILE = r"./memory.txt"  # 使用相对路径，放在代码同目录
MODEL_NAME = "qwen:7b"  # 或者你实际用的模型名，如"deepseek-r1:7b"
# ====================================================================
OLLAMA_API_CHAT = "http://localhost:11434/api/chat"  # Ollama默认API地址

def init_memory_file():
    """初始化记忆文件（不存在则创建）"""
    if not os.path.exists(MEMORY_FILE):
        # 自动创建文件夹（避免路径不存在）
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            f.write(f"【对话记忆开始】- 创建时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"✅ 已创建记忆文件：{MEMORY_FILE}")
    else:
        print(f"✅ 记忆文件已存在：{MEMORY_FILE}")

def read_memory():
    """读取memory.txt的最近10条记忆（适配你的模型人设）"""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("【对话记忆开始】")]
        # 只取最近10条，避免记忆过长
        recent_memory = "\n".join(lines[-10:]) if lines else "暂无过往记忆"
        return f"【温卿卿的专属记忆】\n{recent_memory}"
    except Exception as e:
        return f"读取记忆失败：{str(e)}"

def write_to_memory(role, content):
    """实时写入对话到memory.txt（追加模式，不覆盖）"""
    if not content.strip():
        return
    # 格式化时间戳，和你原有记忆格式一致
    time_str = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{time_str} {role}：{content}\n"
    try:
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(line)
        print(f"📝 记忆已保存：{line.strip()}")
    except Exception as e:
        print(f"⚠️ 写入记忆失败：{str(e)}")

def get_model_reply(user_content):
    """调用Ollama API（适配你的ChatML格式Modelfile）"""
    # 构建符合你Modelfile的请求格式（仅传递user消息，system由Modelfile处理）
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": user_content}],
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_ctx": 8192
        }
    }
    try:
        # 发送请求到Ollama API
        response = requests.post(
            OLLAMA_API_CHAT,
            json=payload,
            timeout=300,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()  # 捕获HTTP错误
        # 提取并清理模型回复（过滤特殊标记）
        raw_reply = response.json()["message"]["content"]
        # 移除模型输出的多余标记，只保留纯文本
        clean_reply = raw_reply.replace("<|im_end|>", "").replace("<popup>", "").strip()
        return clean_reply if clean_reply else "卿卿～我在呢❤️"
    except requests.exceptions.ConnectionError:
        return "❌ 连接失败：请确认Ollama服务已启动（ollama serve）"
    except Exception as e:
        return f"❌ 回复获取失败：{str(e)}"

def main_chat():
    """主聊天逻辑（核心功能：读记忆→聊天→写记忆）"""
    print("="*60)
    print(f"🎉 温卿卿专属 - {MODEL_NAME} 记忆聊天工具")
    print(f"📌 记忆文件：{MEMORY_FILE}")
    print(f"💡 输入 /exit 退出聊天 | 输入 /clear 清空记忆")
    print("="*60 + "\n")

    # 读取过往记忆（供模型参考）
    memory_content = read_memory()
    print(f"📖 已加载过往记忆：\n{memory_content}\n")

    while True:
        # 获取用户输入
        user_input = input("你：").strip()
        
        # 退出指令
        if user_input == "/exit":
            print("\n👋 聊天结束，所有对话已保存到记忆文件！")
            break
        
        # 清空记忆指令
        if user_input == "/clear":
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                f.write(f"【对话记忆开始】- 创建时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            print("✅ 已清空所有记忆！\n")
            memory_content = "暂无过往记忆"
            continue
        
        # 空输入跳过
        if not user_input:
            print("⚠️ 请输入有效内容！\n")
            continue

        # 1. 写入用户输入到记忆文件
        write_to_memory("你", user_input)
        
        # 2. 构建带记忆的完整提问（把过往记忆传给模型）
        full_input = f"{memory_content}\n\n卿卿当前说：{user_input}"
        
        # 3. 获取模型回复（加载中提示）
        print("年年正在温柔回应中...")
        assistant_reply = get_model_reply(full_input)
        
        # 4. 写入模型回复到记忆文件
        write_to_memory("年年", assistant_reply)
        
        # 5. 显示模型回复（更新记忆内容）
        print(f"年年：{assistant_reply}\n")
        memory_content = read_memory()  # 刷新记忆

if __name__ == "__main__":
    # 自动安装依赖（首次运行）
    required_packages = ["requests"]
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            print(f"📦 正在安装依赖包 {pkg}（仅首次运行）...")
            os.system(f"pip install {pkg} -i https://pypi.tuna.tsinghua.edu.cn/simple")
    
    # 初始化记忆文件
    init_memory_file()
    
    # 启动聊天（异常捕获，防止闪退）
    try:
        main_chat()
    except KeyboardInterrupt:
        print("\n👋 聊天被中断，已保存当前对话到记忆文件！")
    except Exception as e:
        print(f"\n❌ 程序异常：{str(e)}")
        input("按任意键退出...")
