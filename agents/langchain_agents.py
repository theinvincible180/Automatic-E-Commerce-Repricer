import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from agents.tools import (
    scrape_competitor_prices_tool,
    get_all_product_ids_tool,
    get_product_pricing_data_tool,
    calculate_optimal_price_tool,
    execute_price_update_tool,
)

load_dotenv()


def get_llm():
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )


def run_monitoring_agent():
    """
    In LangGraph, create_react_agent returns a compiled graph
    that you invoke directly with a messages list.
    No AgentExecutor needed — the graph handles the loop itself.
    """
    llm = get_llm()
    tools = [scrape_competitor_prices_tool, get_all_product_ids_tool]

    agent = create_react_agent(llm, tools)

    result = agent.invoke({
        "messages": [
            SystemMessage(content=(
                "You are a Market Monitoring Agent. "
                "Your job is to scrape competitor prices for all products. "
                "First check what products exist, then scrape all prices."
            )),
            HumanMessage(content=(
                "Scrape all competitor prices for all products in the database "
                "and confirm when done."
            ))
        ]
    })

    # The final message in the list is the agent's answer
    return result["messages"][-1].content


def run_margin_agent():
    llm = get_llm()
    tools = [
        get_all_product_ids_tool,
        get_product_pricing_data_tool,
        calculate_optimal_price_tool,
    ]

    agent = create_react_agent(llm, tools)

    result = agent.invoke({
        "messages": [
            SystemMessage(content=(
                "You are a Risk and Margin Analysis Agent. "
                "Analyse competitor prices against cost and margin rules. "
                "Get all products first, then analyse each one by one."
            )),
            HumanMessage(content=(
                "Get all product IDs, then for each product get its pricing data "
                "and calculate the optimal price. Summarise your findings."
            ))
        ]
    })

    return result["messages"][-1].content


def run_execution_agent(margin_summary: str):
    llm = get_llm()
    tools = [get_all_product_ids_tool, execute_price_update_tool]

    agent = create_react_agent(llm, tools)

    result = agent.invoke({
        "messages": [
            SystemMessage(content=(
                "You are a Price Execution Agent. "
                "Execute price updates for products that need repricing. "
                "Be precise — report exactly what changed and what didn't."
            )),
            HumanMessage(content=(
                f"The margin agent found: {margin_summary}\n\n"
                "Now get all product IDs and execute price updates for each "
                "product that needs repricing. Report what was changed."
            ))
        ]
    })

    return result["messages"][-1].content