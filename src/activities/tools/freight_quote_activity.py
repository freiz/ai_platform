import os
import json
from typing import Any, Dict

import requests

from src.activities import Parameter
from src.activities.activity_registry import ActivityRegistry
from src.activities.tools.tool_activity import ToolActivity


@ActivityRegistry.register_activity(
    activity_type_name='freight_quote_activity',
    description="calculate freight quote based on quote details, by https://truckquote.com/",
    required_params={
        'activity_name': Parameter(name='activity_name', type='string'),
    },
    allow_custom_params=False
)
class FreightQuoteActivity(ToolActivity):
    # Define fixed parameters at class level
    fixed_input_params = {
        'quote_details': Parameter(name='quote_details', type="object", properties={
            'equipment_type': Parameter(name='equipment_type', type="string"),
            'feet': Parameter(name='feet', type="number"),
            'weight_lbs': Parameter(name='weight_lbs', type="number"),
            'date': Parameter(name='date', type="string"),
            'origin': Parameter(name='origin', type="object", properties={
                'address': Parameter(name='address', type="string"),
                'city': Parameter(name='city', type="string"),
                'state': Parameter(name='state', type="string"),
            }),
            'destination': Parameter(name='destination', type="object", properties={
                'address': Parameter(name='address', type="string"),
                'city': Parameter(name='city', type="string"),
                'state': Parameter(name='state', type="string"),
            }),
        }),
    }
    fixed_output_params = {
        'response_json': Parameter(name='response_json', type="string")
    }

    def run(self, quote_details) -> Dict[str, Any]:
        base_url = 'https://api.truckquote.com/api/v1/quotes'
        token = os.environ['TRUCKQUOTE_API_KEY']
        request = {
            'equipment_type': quote_details['equipment_type'], # Allowed values: Flatbeds, Vans, Reefers
            'feet': quote_details['feet'],
            'weight': quote_details['weight_lbs'],
            'weight_unit': 'lbs',
            'date': quote_details['date'], # Format: MM/DD/YYYY
            'stops': [
                {
                    'address': quote_details['origin']['address'],
                    'city': quote_details['origin']['city'],
                    'state': quote_details['origin']['state'],
                },
                {
                    'address': quote_details['destination']['address'],
                    'city': quote_details['destination']['city'],
                    'state': quote_details['destination']['state'],
                }
            ]
        }

        response = requests.post(base_url, headers={'Authorization': f'{token}'}, json=request)
        return {'response_json': json.dumps(response.json(), indent=2)}
