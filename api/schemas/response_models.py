from pydantic import BaseModel, Field

class PickingResponse(BaseModel):
    paths: list[list[dict]]
    summaries: list[list[dict[str, str | int]]]