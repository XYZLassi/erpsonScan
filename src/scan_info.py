from pydantic import BaseModel, Field


class ScanInfo(BaseModel):
    work_directory: str
    work_directory_is_temporary: bool
    output_filename: str | None = None
    files: list[str] = Field(default_factory=list)
    merge_file: str | None = None
