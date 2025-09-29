from datetime import datetime

class Feedback:
    def __init__(self, project_id: int, text: str, created_at: datetime = None):
        self.project_id = project_id
        self.text = text
        self.created_at = created_at or datetime.now()

    def __repr__(self):
        return f"<Feedback project_id={self.project_id} created_at={self.created_at} text={self.text!r}>"