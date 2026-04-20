from pydantic import BaseModel, Field


class FinalDecisionCreate(BaseModel):
    final_outcome: str = Field(pattern="^(kill|iterate|scale)$")
    confidence: int = Field(ge=1, le=10)
    rationale: str = Field(min_length=10)
    owner: str = Field(min_length=2)


class PostmortemCreate(BaseModel):
    what_worked: str = Field(min_length=10)
    what_failed: str = Field(min_length=10)
    key_risks: str = Field(min_length=10)
    next_action: str = Field(pattern="^(kill|iterate|scale)$")
    lessons: str = Field(min_length=10)
