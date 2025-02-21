from dataclasses import dataclass


@dataclass
class GenVideosTask:
    user_id: str
    task_id: str
    submit_time: float
    title: str
    tags: [str]
