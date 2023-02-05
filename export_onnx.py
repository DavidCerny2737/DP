import app.detect

import torch.nn as nn
import torch
import onnx
import onnxruntime
import numpy as np


IMAGE_SIZE = (320, 416)
MODEL_NAME = 'C:\\DP\\app\\YOLOv4-CSP.onnx'


def to_numpy(tensor):
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()


if __name__ == '__main__':
    config = detect.provide_default_config()
    config['onnx'] = False
    config['img-size'] = IMAGE_SIZE
    model = detect.Model(config)

    input = torch.randn((1, 3, IMAGE_SIZE[0], IMAGE_SIZE[1]), device=model.device).half()
    output = model.model.forward(input)

                # Export the model
    torch.onnx.export(model.model,  # model being run
                      input,  # model input (or a tuple for multiple inputs)
                      MODEL_NAME,  # where to save the model (can be a file or file-like object)
                      export_params=True,  # store the trained parameter weights inside the model file
                      opset_version=13,  # the ONNX version to export the model to
                      do_constant_folding=True,  # whether to execute constant folding for optimization
                      input_names=['input'],  # the model's input names
                      output_names=['output'])  # the model's output names)

    onnx_model = onnx.load(MODEL_NAME)
    onnx.checker.check_model(onnx_model)

    ort_session = onnxruntime.InferenceSession(MODEL_NAME, providers=['CUDAExecutionProvider'])
    # compute ONNX Runtime output prediction
    # ort_inputs = {ort_session.get_inputs()[0].name: to_numpy(input)}
    # ort_outs = ort_session.run(None, ort_inputs)

    # compare ONNX Runtime and PyTorch results
    # np.testing.assert_allclose(to_numpy(output[0]), ort_outs[0], rtol=1e-03, atol=1e-05)
    print('vsechno cajk')