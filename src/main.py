from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from tools import wikipedia_tool, fetch_latest_headlines, convert_text_to_pdf, get_financial_statement
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini")

fundamental_agent = create_react_agent(
    model=llm,
    tools=[get_financial_statement],
    prompt=(
        "You are an agent that can answer general questions related to finance.\n\n"
        "You are an agent that can tell us the date of today.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with tasks that require basic knowledge about finance, such as getting the financial statement.\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    ),
    name="fundamental"
)

market_industry_agent = create_react_agent(
    model=llm,
    tools=[fetch_latest_headlines, wikipedia_tool],
    prompt=(
        "You are a finance research agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with research-related tasks, including finding the recent financial news, and looking-up factual information and stock data. DO NOT write any code.\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    ),
    name="market_industry"
)

config = {"configurable": {"thread_id": "1", "user_id": "1"}}
checkpointer = InMemorySaver()

supervisor = create_supervisor(
    model=llm,
    agents=[fundamental_agent, market_industry_agent],
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- a fundamental agent. Assign the queries about financial statement to this agent\n"
        "- a market industry agent. Assign market industry related research tasks to this agent\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    ),
    add_handoff_back_messages=True,
    output_mode='full_history'
).compile(checkpointer=checkpointer)

user_query = input("Enter your query ('q' to quit): ")

for chunk in supervisor.stream({
    'messages': [
        {'role': 'user', 'content': user_query}
    ]},
    config=config
):
    print(chunk)