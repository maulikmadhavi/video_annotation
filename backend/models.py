class Annotation:
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time

    def to_dict(self):
        return {"start_time": self.start_time, "end_time": self.end_time}

    @staticmethod
    def from_dict(data):
        return Annotation(data["start_time"], data["end_time"])
