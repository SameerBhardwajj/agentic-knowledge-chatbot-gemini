
from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from .config import GEMINI_API_KEY, GEMINI_MODEL, SYSTEM_PROMPT
from .rag import format_context, retrieve_knowledge
from .tools import GET_CURRENT_USER_PROFILE_TOOL, get_current_user_profile

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(api_key=GEMINI_API_KEY)
tool = types.Tool(function_declarations=[GET_CURRENT_USER_PROFILE_TOOL])

def run_agent(db: Session, current_user_id: int, user_message: str,
              history: list[tuple[str, str]]):
    kb_results = retrieve_knowledge(db, user_message)
    kb_context = format_context(kb_results)

    contents = []
    for role, content in history:
        contents.append(types.Content(
            role="model" if role == "assistant" else "user",
            parts=[types.Part.from_text(text=content)],
        ))

    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(
            text=f"KNOWLEDGE BASE CONTEXT:\n{kb_context}\n\nUSER REQUEST:\n{user_message}"
        )],
    ))

    tools_used = []

    for _ in range(4):
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[tool],
            ),
        )

        candidate = response.candidates[0]
        contents.append(candidate.content)
        function_calls = response.function_calls or []

        if not function_calls:
            return (
                response.text or "I don't have that information in the knowledge base.",
                kb_results,
                tools_used,
            )

        for call in function_calls:
            if call.name != "get_current_user_profile":
                continue

            result = get_current_user_profile(db, current_user_id)
            tools_used.append(call.name)

            function_response = types.Part.from_function_response(
                name=call.name,
                response={"result": result},
                # id=call.id,
            )
            contents.append(types.Content(
                role="user",
                parts=[function_response],
            ))

    return "I couldn't complete the request safely.", kb_results, tools_used
