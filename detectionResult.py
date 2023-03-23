import json


class DetectionResult:

    def __init__(self, x, y, width, height, confidence, class_index):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.confidence = confidence.item()
        self.class_index = class_index.item()

    def to_json(self):
        return json.dumps({
            'position': {
                'x': str(self.x),
                'y': str(self.y),
                'width': str(self.width),
                'height': str(self.height)
            },
            'confidence': self.confidence,
            'class': self.class_index
        })
