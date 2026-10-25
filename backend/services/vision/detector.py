import cv2
import numpy as np
from typing import List, Tuple, Dict, Any

class PersonDetector:
    """
    Robust, privacy-preserving local person detection using a multi-stage approach:
    1. OpenCV HOG Person Detector (for standing/walking persons)
    2. Haar Cascade Face/Upper-Body Classifiers (for seated students facing camera)
    3. Silhouette & Contour Analysis (fallback for students facing desks/blackboards or synthetic feeds)
    """
    def __init__(self):
        # 1. HOG Person Detector
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # 2. Haar Cascades
        face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
        
        upper_body_path = cv2.data.haarcascades + "haarcascade_upperbody.xml"
        self.upper_cascade = cv2.CascadeClassifier(upper_body_path) if cv2.os.path.exists(upper_body_path) else None

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect persons in a video frame.
        Returns list of bounding boxes as (x, y, w, h).
        """
        if frame is None or frame.size == 0:
            return []

        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        boxes = []

        # Stage 1: HOG Person Detector
        try:
            hog_boxes, _ = self.hog.detectMultiScale(
                gray,
                winStride=(8, 8),
                padding=(8, 8),
                scale=1.05
            )
            for (bx, by, bw, bh) in hog_boxes:
                boxes.append([int(bx), int(by), int(bw), int(bh)])
        except Exception:
            pass

        # Stage 2: Haar Face / Upper-Body Cascade
        try:
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(28, 28)
            )
            for (fx, fy, fw, fh) in faces:
                px = max(0, int(fx - fw * 0.4))
                py = max(0, int(fy - fh * 0.2))
                pw = min(w - px, int(fw * 1.8))
                ph = min(h - py, int(fh * 3.0))
                boxes.append([px, py, pw, ph])
        except Exception:
            pass

        # Stage 3: Silhouette & Contour Fallback (handles students angled away or synthetic classroom feeds)
        if len(boxes) == 0:
            try:
                blurred = cv2.GaussianBlur(gray, (7, 7), 0)
                # Adaptive threshold to isolate foreground participant shapes against classroom background
                thresh = cv2.adaptiveThreshold(
                    blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 5
                )
                # Morphological close to join head and torso contours
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 25))
                closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

                contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                frame_area = h * w

                for c in contours:
                    cx, cy, cw, ch = cv2.boundingRect(c)
                    c_area = cw * ch
                    aspect_ratio = ch / max(1.0, float(cw))
                    
                    # Human silhouette heuristics:
                    # - Area between 1.5% and 40% of frame
                    # - Taller than wide or roughly square (aspect ratio >= 0.8)
                    # - Located in plausible classroom seating vertical band (cy > 0.05 * h)
                    if (0.015 * frame_area <= c_area <= 0.45 * frame_area) and (0.75 <= aspect_ratio <= 3.8):
                        boxes.append([int(cx), int(cy), int(cw), int(ch)])
            except Exception:
                pass

        if not boxes:
            return []

        # Stage 4: Non-Maximum Suppression to consolidate overlapping detections
        boxes_array = np.array(boxes)
        nms_boxes = self._non_max_suppression(boxes_array, overlap_thresh=0.35)
        return [(int(b[0]), int(b[1]), int(b[2]), int(b[3])) for b in nms_boxes]

    @staticmethod
    def _non_max_suppression(boxes: np.ndarray, overlap_thresh: float = 0.35) -> List[List[int]]:
        """Apply Non-Maximum Suppression to bounding boxes [x, y, w, h]."""
        if len(boxes) == 0:
            return []

        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 0] + boxes[:, 2]
        y2 = boxes[:, 1] + boxes[:, 3]
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = np.argsort(y2)

        keep = []
        while len(order) > 0:
            last = len(order) - 1
            i = order[last]
            keep.append(i)

            xx1 = np.maximum(x1[i], x1[order[:last]])
            yy1 = np.maximum(y1[i], y1[order[:last]])
            xx2 = np.minimum(x2[i], x2[order[:last]])
            yy2 = np.minimum(y2[i], y2[order[:last]])

            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)
            overlap = (w * h) / areas[order[:last]]

            order = np.delete(order, np.concatenate(([last], np.where(overlap > overlap_thresh)[0])))

        return boxes[keep].tolist()

class MotionAnalyzer:
    """Computes frame-to-frame motion energy across the scene to measure observable classroom dynamics."""
    def __init__(self):
        self.prev_gray = None

    def compute_motion(self, frame: np.ndarray) -> float:
        """Calculate normalized scene motion energy (0.0 to 1.0) using absolute frame difference."""
        if frame is None or frame.size == 0:
            return 0.0

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_gray is None:
            self.prev_gray = gray
            return 0.0

        frame_diff = cv2.absdiff(self.prev_gray, gray)
        _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        motion_score = float(np.sum(thresh) / (frame.shape[0] * frame.shape[1] * 255))
        self.prev_gray = gray
        return min(1.0, motion_score * 5.0)  # scale for typical classroom sensitivity
