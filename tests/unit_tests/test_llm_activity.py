from src.activities import LLMActivity, Parameter, ParamType
from src.utils.llm import LLMConfig

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


def test_capital_finder_dump():
    model_json = capital_finder.model_dump_json(exclude_none=True, indent=4)
    print(f'\n{model_json}')


def test_capital_finder_output_schema():
    schema = capital_finder._create_output_json_schema()
    print(f'\n{schema}')


def test_capital_finder_system_message():
    system_message = capital_finder._add_output_type()
    print(f'\n{system_message}')
