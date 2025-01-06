from pydantic import BaseModel, Field

class PickingResponse(BaseModel):
    paths: list[list[dict]]
    summaries: list[dict[str, dict[str, dict[str, int]]]]