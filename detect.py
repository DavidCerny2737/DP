import base64

import psutil
import onnxruntime
from numpy import random

from utils.plots import plot_one_box
from utils.torch_utils import select_device, time_synchronized
from export_onnx import MODEL_NAME


from models.models import *
from utils.datasets import *
from utils.general import *
from utils.recognition import remove_old_representants, check_face


def provide_default_config():
    return {'weights': ['best.pt'], 'img-size': 640, 'conf-thres': 0.4, 'iou-thres': 0.6, 'device': '0', 'view-img': True,
            'save-txt': False, 'agnostic-nms': True, 'augment': False, 'update': False, 'cfg': 'models/yolov4-csp.cfg',
            'names': 'data/coco.names', 'save-img': False, 'classes': None, 'onnx': True}


class Model:

    def __init__(self, config):
        # Initialize
        self.weights = config['weights']
        self.onnx = config['onnx']
        self.view_img = config['view-img']
        self.save_txt = config['save-txt']
        self.img_size = config['img-size']
        self.save_img = config['save-img']
        self.conf_thres = config['conf-thres']
        self.iou_thres = config['iou-thres']
        self.device = select_device(config['device'])
        self.agnostic_nms = config['agnostic-nms']
        self.augment = config['augment']
        self.classes = config['classes']
        self.update = config['update']
        self.cfg = config['cfg']
        self.half = self.device.type != 'cpu'
        if self.onnx:
            assert 'CUDAExecutionProvider' in onnxruntime.get_available_providers()
            sess_options = onnxruntime.SessionOptions()
            sess_options.intra_op_num_threads = psutil.cpu_count(logical=True)
            self.model = onnxruntime.InferenceSession(MODEL_NAME, sess_options, providers=['CUDAExecutionProvider'])
        else:
            self.model = Darknet(self.cfg, self.img_size).cuda()
        self.safe_path = 'test-network.png'

        # Load model
        if not self.onnx:
            try:
                self.model.load_state_dict(torch.load(self.weights[0], map_location=self.device)['model'])
                # model = attempt_load(weights, map_location=device)  # load FP32 model
                # imgsz = check_img_size(imgsz, s=model.stride.max())  # check img_size
            except:
                load_darknet_weights(self.model, self.weights[0])
            self.model.to(self.device).eval()
            if self.half:
                self.model.half()  # to FP16

        # Get names and colors
        self.names = load_classes(config['names'])
        self.colors = [[random.randint(0, 255) for _ in range(3)] for _ in range(len(self.names))]

    @torch.inference_mode()
    def forward(self, base64_image, auto_size=32):
        t0 = time.time()

        im0s = np.frombuffer(base64_image, np.uint8)
        im0s = cv2.imdecode(im0s, cv2.IMREAD_COLOR)

        # Padded resize
        img = letterbox(im0s, new_shape=self.img_size, auto_size=auto_size)[0]
        # Convert
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
        img = np.ascontiguousarray(img)

        if self.onnx:
            img = np.float16(img) if self.half else np.float32(img)
            img /= 255.0
            img = np.expand_dims(img, 0)
        else:
            img = torch.from_numpy(img).to(self.device)
            img = img.half() if self.half else img.float()  # uint8 to fp16/32
            img /= 255.0  # 0 - 255 to 0.0 - 1.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)



        # Inference
        t1 = time_synchronized()
        if self.onnx:
            ort_inputs = {self.model.get_inputs()[0].name: img}
            pred = self.model.run(None, ort_inputs)[0]
            pred = torch.from_numpy(pred)
        else:
            pred = self.model(img, augment=self.augment)[0]

        # Apply NMS
        pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, classes=self.classes,
                                           agnostic=self.agnostic_nms)
        t2 = time_synchronized()

        # Apply Classifier
        #if classify:
        #    pred = apply_classifier(pred, modelc, img, im0s)

        # Process detections
        det = pred[0]  # detections per image
        s, im0 = '', im0s

        s += '%gx%g ' % img.shape[2:]  # print string
        gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
        if det is not None and len(det):
             # Rescale boxes from img_size to im0 size
            det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

            # Print results
            for c in det[:, -1].unique():
                n = (det[:, -1] == c).sum()  # detections per class
                s += '%g %ss, ' % (n, self.names[int(c)])  # add to string

            # Write results
            for *xyxy, conf, cls in det:
                if self.save_txt:  # Write to file
                    xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(
                        -1).tolist()  # normalized xywh
                    with open(txt_path + '.txt', 'a') as f:
                        f.write(('%g ' * 5 + '\n') % (cls, *xywh))  # label format

                if self.view_img:  # Add bbox to image
                    if int(cls) == 1:
                        print('Unmask detected!')
                        c1, c2 = (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3]))
                        face = im0[c1[1]:c2[1], c1[0]:c2[0]]
                        # check_face(face, im0)

                        t = Thread(target=check_face, args=(face, im0))
                        t.start()

                    label = '%s %.2f' % (self.names[int(cls)], conf)
                    plot_one_box(xyxy, im0, label=label, color=self.colors[int(cls)], line_thickness=3)

        # Print time (inference + NMS)
        print('%sDone inference. (%.3fs)' % (s, t2 - t1))
        print('Done full. (%.3fs)' % (time.time() - t0))
        _, image = cv2.imencode('.png', im0)
        return base64.b64encode(image).decode()


def load_classes(path):
    # Loads *.names file at 'path'
    with open(path, 'r') as f:
        names = f.read().split('\n')
    return list(filter(None, names))  # filter removes empty strings (such as last line)
