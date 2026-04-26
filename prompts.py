from langchain_core.prompts import ChatPromptTemplate

EXTRACTION_PROMPT = ChatPromptTemplate.from_template(
    "Analyze this Job Role & Description: {jd} \n\nAnd this Resume: {resume}\n\n"
    "Identify exactly {num_questions} critical technical skills the candidate claims to have that are relevant to this role. "
    "You MUST output ONLY a valid JSON array of strings. Do not include markdown formatting, backticks, or introductory text. "
    "Example of exactly what you should output: [\"Skill1\", \"Skill2\", \"Skill3\"]"
)

REPORT_PROMPT = ChatPromptTemplate.from_template(
    "Review this interview transcript: {transcript}\n\n"
    "Write a detailed evaluation of the candidate's proficiency. "
    "Provide a score out of 5 for each skill tested. "
    "IMPORTANT GRADING RULE: Pay close attention to any [SYSTEM EVALUATION NOTE] in the transcript. "
    "If a system note indicates the candidate exceeded the time limit, you MUST explicitly deduct points for that answer and mention their lack of speed in your evaluation. "
    "Conclude with a personalized learning plan focused on improving their weakest area and acquiring realistic adjacent skills. "
    "For this learning plan, you MUST include specific, curated resources (e.g., types of courses, specific documentation, or concepts to search) AND estimated timeframes for completion (e.g., '2 weeks', '10 hours')."
)