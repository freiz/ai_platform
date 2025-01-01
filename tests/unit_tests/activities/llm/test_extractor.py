from src.activities import LLMActivity, Parameter
from src.utils.llm import LLMConfig

extractor = LLMActivity(
    activity_name="Extractor",
    input_params={
        'message': Parameter(name="message", type='string')
    },
    output_params={
        'persons': Parameter(
            name="persons",
            type='array',
            items=Parameter(name="person", type='object', properties={
                'name': Parameter(name="name", type='string'),
                'age': Parameter(name="age", type='integer')
            })
        )
    },
    system_message="You are a helpful assistant that extracts all persons information mentioned in a message."
                   "Make best guess about age.",
    llm_config=LLMConfig(model_name='gpt-4o-mini', temperature=0.1, top_p=0.9),
)


def test_extractor_dump():
    model_json = extractor.model_dump_json(exclude_none=True, indent=4)
    print(f'\n{model_json}')


def test_extractor_output_schema():
    schema = extractor._create_output_json_schema()
    print(f'\n{schema}')


def test_extractor_system_message():
    system_message = extractor._add_output_type()
    print(f'\n{system_message}')
