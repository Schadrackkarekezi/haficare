from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from typing import Dict

# Placeholder data. In reality this would live in your database.

doctor_data = [
    {
        'id': 1,
        'name': 'Dr. ABC',
        'city': 'Kigali',
        'specialty': 'Oncology'
    },
    {
        'id': 2,
        'name': 'Dr. DEF',
        'city': 'Gisenye',
        'specialty': 'Optometry'
    },
    {
        'id': 3,
        'name': 'Dr. GHI',
        'city': 'Butare',
        'specialty': 'Oncology'
    },
    {
        'id': 4,
        'name': 'Dr. JKL',
        'city': 'Butare',
        'specialty': 'Pediatrics'
    },
    {
        'id': 5,
        'name': 'Dr. MNO',
        'city': 'Kigali',
        'specialty': 'Pediatrics'
    },
]

"""Define what information the model requires in order to run. In particular we'll need:
- The `data` which has all the doctors in it
"""

@dataclass
class ModelDependencies:
  data: doctor_data

"""Next we define what the model will output after it has finished its processing. Here we expect it to output:
- A `doctor_name`
- The `doctor_city`
- The `doctor_specialty`
"""

class ModelOutput(BaseModel):
  doctor_name: str = Field(description='Name of the recommended doctor')
  doctor_city: str = Field(description='The city the doctor works in')
  doctor_specialty: str = Field(description="The doctor's specialty")

"""Next we'll define the agent which will:
- Interact with the user to get the required information
- Query the `data` to find an appropriate doctor
- Return the appropriate `ModelOutput` to the user
"""

support_agent = Agent(
    'openai:gpt-4o-mini',
    deps_type = ModelDependencies,
    output_type = ModelOutput,
    system_prompt = (
        'You are a support agent helping patients in Rwanda find a nearby doctor '
        'matching their desired city. Only look in the data supplied in the dependencies. '
        'If you are unable to find a matching doctor, return "N/A" for all values.'
    )
)

"""We'll need to provide the agent with some tools in order to accomplish this. In particular, we'll given the agent the following two tools:
- Search in the data for all doctors in a given city
- Search in the data for the information for a doctor, given the doctors id

The logic is that the agent will:
1. Extract from the query the city the user is interested in
2. Query the data using the tool just described
3. Get the id for the (first) doctor found that works in that city
4. Query the data using the second tool described to find the info on the doctor with this id
5. Present this information to user in the form specified in `ModelOutupt`
"""

def find_ids_by_city(doctor_data, value):
  """
  Find the ids for all doctors in the given city
  """
  return [d['id'] for d in doctor_data if d['city'] == value][0]

def find_doctor_by_id(doctor_data, id):
  """
  Find the doctor with a given id
  """
  return [d for d in doctor_data if d['id'] == id][0]

@support_agent.tool
async def tool_find_ids_by_city(
    ctx: RunContext[ModelDependencies],
    city: str
) -> int:
  return find_ids_by_city(ctx.deps.data, city)

@support_agent.tool
async def tool_find_doctor_by_id(
    ctx: RunContext[ModelDependencies],
    id: int
) -> Dict:
  return find_doctor_by_id(ctx.deps.data, id)

async def run_agent():
    deps = ModelDependencies(data = doctor_data)

    result = await support_agent.run('Find me a doctor in Butare.', deps=deps)
    print(result.output)
