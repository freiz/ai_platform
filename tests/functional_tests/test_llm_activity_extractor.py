from dotenv import load_dotenv

from src.activities import LLMActivity, Parameter
from src.utils.llm import LLMConfig

load_dotenv_succeeded = load_dotenv('.env')
assert load_dotenv_succeeded

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


def test_extractor():
    inputs = {
        'message': '''
Dorn, a 3,000 year old silver Space dragon, has only wanted two things in his life: revenge, and the time necessary to get that revenge.

Kiera is a migrant farm worker, running from a troubled past, and doesn't expect the rest of her life to go anywhere.  She's already given up hope of ever going back to her homeland with her head held high, and getting justice against those who drove her away.

Dorn builds a dungeon in the hopes of amassing a trained human army for his vengeance, and Kiera takes the chance to help, hoping for reciprocation.  But the past is a murky thing; events are not always what they seem, and those who should be allies are frequently the greatest of enemies. 
        '''
    }
    outputs = extractor(**inputs)
    print(f'\n{outputs}')
    assert 'persons' in outputs
    assert len(outputs['persons']) == 2

    names = sorted([person['name'] for person in outputs['persons']])
    assert names == ['Dorn', 'Kiera']


