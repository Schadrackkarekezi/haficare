from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

"""
I will define an agent to determine whether the patient is looking for a doctor, looking for a medication, or asking about symptoms.
If the patient is asking about symptoms, then I want to determine what specialty would be best suited to help them.
If they're looking for a medication, I need to know the name of that medication.
"""

specialty_data = [
    {
        'id': 1,
        'specialty': 'General pracitioner',
        'symptoms': ['fever', 'headache', 'nausea']
    },
    {
        'id': 2,
        'specialty': 'Oncology',
        'symptoms': ['cough', 'weight loss', 'fatigue']
    },
    {
        'id': 3,
        'specialty': 'Optometry',
        'symptoms': ['blurred vision', 'eye pain']
    },
    {
        'id': 4,
        'specialty': 'Pediatrics',
        'symptoms': ['fever', 'cough', 'vomiting', 'child']
    }
]

@dataclass
class ModelDependencies:
  data: specialty_data
  
  
class ModelOutput(BaseModel):
  target: str = Field(description="One of unknown, doctor, medication, or symptoms")
  
  
support_agent = Agent(
    'openai:gpt-4o-mini',
    deps_type = ModelDependencies,
    output_type = ModelOutput,
    system_prompt = (
        '''You are a support agent for a medical application. The user may be asking about doctors,
        medication, or symptoms. Your job is to determine what the user is asking about and return the appropriate
        response. By default the target is "unknown", which means we don't yet know what the user is asking about.
        If you determine they're asking for a doctor, then the target is "doctor". If you determine they're asking for a medication,
        then the target is "medication". If you determine they're asking about symptoms, then the target is "symptoms".'''
    )
)

# Write a function which goes through my data and finds the specialty which matches the symptoms
def find_specialty_by_symptoms(data, symptom) -> int:
    return False

@support_agent.tool
async def tool_find_specialty_by_symptoms(
    ctx: RunContext[ModelDependencies],
    symptom: str
) -> int:
  return find_specialty_by_symptoms(ctx.deps.data, symptom)