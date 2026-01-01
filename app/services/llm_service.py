from openai import OpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI  
import os
import json
from app.core.config import settings

class LLMService:
    def __init__(self):
        # 确保你的 .env 文件中有 OPENAI_API_KEY
        # 这样即使环境变量没设置，Pydantic 也会在启动时报错，而不是运行到一半报错
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        
    def get_rag_chat_response(self, context: str, user_answer: str, chat_history: list):
        """
        基于检索到的简历片段进行模拟面试对话
        """
        messages = [
            SystemMessage(content=(
                "你是一个专业的面试官。以下是应聘者简历的部分相关内容：\n"
                f"---简历上下文---\n{context}\n----------------\n"
                "请结合上述简历信息和之前的对话历史，对用户的回答做出评价，并提出下一个面试问题。"
                "注意：不要脱离简历内容生造问题。如果简历中没提到相关背景，请围绕通用技能提问。"
            ))
        ]
        
        # ✅ 修复：这里必须改为 chat_history，与参数名保持一致
        for msg in chat_history: 
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        # 填充当前回答
        messages.append(HumanMessage(content=user_answer))
        
        response = self.model.invoke(messages)
        return response.content
    
    def analyze_resume(self, text: str):
        """将原始文本转换为结构化 JSON"""
        prompt = "Extract name, contact, skills, and experience into JSON format from this resume text."
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON. Include 'json' in your response."},
                {"role": "user", "content": f"{prompt}\n\n{text}"}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def generate_first_question(self, resume_text: str, context: str = ""):
        """根据简历生成面试问题"""
        system_prompt = (
            "You are a senior technical interviewer at a big tech company. "
            "Based on the candidate's resume, ask a challenging technical question "
            "related to their projects or skills. Be professional and concise."
        )
        user_content = f"Resume context: {resume_text}\n\nCandidate's last message: {context}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        return response.choices[0].message.content
    
    def get_chat_response(self, resume_text, user_answer, chat_history):
        system_prompt = f"你是一个专业面试官。这是候选人的简历：{resume_text}。请根据历史对话和用户最新的回答，给出简短评价并询问下一个问题。"
    
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history) # 加入之前的记忆
        messages.append({"role": "user", "content": user_answer}) # 加入最新的回答

        response = self.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
        )
        return response.choices[0].message.content