import torch
from models.models import *

WEIGHTS = 'yolov4-csp.weights'
RESULT = 'yolov4-csp.pth'


if __name__ == '__main__':
    device = torch.device('cpu')
    model = Darknet('models/yolov4-csp.cfg', 640).to(device)
    load_darknet_weights(model, WEIGHTS)
    torch.save(model.state_dict(), RESULT)