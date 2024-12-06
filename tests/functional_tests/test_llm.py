from dotenv import load_dotenv
from src.utils.llm import LLMConfig, LLM

load_dotenv_succeeded = load_dotenv('.env')
assert load_dotenv_succeeded


def test_call_llm():
    config = LLMConfig(model_name='gpt-4o-mini', temperature=0.2, top_p=1.0)
    llm = LLM(config)
    system_message = "You are a helpful assistant."
    user_message = "What is the capital of France?"
    response = llm.complete(system_message, user_message)
    assert response
