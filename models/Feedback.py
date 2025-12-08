from datetime import datetime

class Feedback:
    def __init__(self, project_id: int, text: str, created_at: datetime = None):
        """
        Initialize a Feedback instance.

        Parameters:
            project_id (int): Identifier of the associated project.
            text (str): The feedback text content.
            created_at (datetime, optional): Timestamp when the feedback was created.
                Defaults to the current local datetime if not provided.

        """
        self.project_id = project_id
        self.text = text
        self.created_at = created_at or datetime.now()

    def __repr__(self):
        """
        Return a concise string representation of the Feedback instance.

        Includes the project_id, created_at timestamp, and the repr-formatted text
        content to aid in debugging and logging.
        """
        return f"<Feedback project_id={self.project_id} created_at={self.created_at} text={self.text!r}>"