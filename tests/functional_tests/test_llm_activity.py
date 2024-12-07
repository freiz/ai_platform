from dotenv import load_dotenv

from src.activities import LLMActivity, Parameter
from src.utils.llm import LLMConfig

load_dotenv_succeeded = load_dotenv('.env')
assert load_dotenv_succeeded

capital_finder = LLMActivity(
    activity_name="CapitalFinder",
    input_params={
        'country': Parameter(name="country", type='string')
    },
    output_params={
        'capital': Parameter(name="capital", type='string')
    },
    system_message="You are a helpful assistant that returns the capital of a country.",
    llm_config=LLMConfig(model_name='gpt-4o-mini', temperature=0.1, top_p=0.9),
)


def test_capital_finder():
    inputs = {'country': 'France'}
    outputs = capital_finder.run(**inputs)
    print(f'\n{outputs}')
    assert outputs['capital'].lower() == 'paris'
