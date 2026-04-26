import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompts import EXTRACTION_PROMPT, REPORT_PROMPT

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3
)

store = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def extract_skills(jd_text: str, resume_text: str, num_questions: int):
    chain = EXTRACTION_PROMPT | llm | JsonOutputParser()
    return chain.invoke({"jd": jd_text, "resume": resume_text, "num_questions": num_questions})

# NEW: Now accepts the dynamic system prompt from the database
def get_interview_chain(custom_system_prompt: str):
    dynamic_prompt = ChatPromptTemplate.from_messages([
        ("system", custom_system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_input}")
    ])
    
    chain = dynamic_prompt | llm | StrOutputParser()
    return RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="user_input",
        history_messages_key="history",
    )

def generate_report(session_id: str):
    history = get_session_history(session_id)
    transcript = "\n".join([f"{msg.type}: {msg.content}" for msg in history.messages])
    chain = REPORT_PROMPT | llm | StrOutputParser()
    return chain.invoke({"transcript": transcript})