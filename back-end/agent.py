from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool, AgentType
import requests
import json
import os
from dotenv import load_dotenv
from config import *

load_dotenv()

llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL)

def recommend_etf(input_text):
    customer_data = json.loads(input_text)
    response = requests.post(
        f"{RAG_API_URL}/recommend-etf",
        json=customer_data
    )
    return response.json()

def rebalance_report(input_text):
    customer_data = json.loads(input_text)
    response = requests.post(
        f"{RAG_API_URL}/rebalance-report",
        json=customer_data
    )
    return response.json()

tools = [
    Tool(
        name="recommend_etf",
        func=recommend_etf,
        description="ETF 미보유 고객에게 ETF를 추천하는데 사용합니다. 고객 투자정보 JSON 필요"
    ),
    Tool(
        name="rebalance_report",
        func=rebalance_report,
        description="ETF 보유 고객에게 리밸런싱 보고서를 제공하는데 사용합니다. 고객 투자정보 JSON 필요"
    )
]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

def agent_run(customer_info):
    prompt = f"""
    고객 투자 정보:
    {customer_info}

    ETF 보유 여부에 따라 ETF 추천 또는 리밸런싱 보고서를 제공해주세요.
    """
    result = agent.run(prompt)
    return result

if __name__ == "__main__":
    customer_without_etf = {
        "customer_id": 1,
        "investment_profile": "공격형",
        "financial_status": "고자산",
        "has_etf": False,
        "etfs_owned": []
    }

    customer_with_etf = {
        "customer_id": 2,
        "investment_profile": "중립형",
        "financial_status": "중자산",
        "has_etf": True,
        "etfs_owned": ["ETF1", "ETF2"]
    }

    print("🔷 ETF 미보유 고객 요청 처리:")
    result_without_etf = agent_run(customer_without_etf)
    print(result_without_etf)

    print("\n🔷 ETF 보유 고객 요청 처리:")
    result_with_etf = agent_run(customer_with_etf)
    print(result_with_etf)
