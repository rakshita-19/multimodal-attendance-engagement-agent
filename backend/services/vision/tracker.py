import numpy as np
from typing import List, Tuple, Dict, Any

class TrackRecord:
    """Encapsulates the lifecycle, spatial trajectory, and presence statistics of a detected participant track."""
    def __init__(self, track_id: int, bbox: Tuple[int, int, int, int], timestamp: float):
        self.track_id = track_id
        self.bbox = bbox  # (x, y, w, h)
        self.centroid = (bbox[0] + bbox[2] / 2.0, bbox[1] + bbox[3] / 2.0)
        self.first_seen_seconds = timestamp
        self.last_seen_seconds = timestamp
        self.total_visible_seconds = 0.0
        self.frames_visible = 1
        self.disappeared_frames = 0
        self.is_active = True
        self.total_movement = 0.0
        self.last_timestamp = timestamp

    def update(self, bbox: Tuple[int, int, int, int], timestamp: float, frame_interval_seconds: float):
        """Update track with new detection bounding box and timestamp."""
        new_centroid = (bbox[0] + bbox[2] / 2.0, bbox[1] + bbox[3] / 2.0)
        dx = new_centroid[0] - self.centroid[0]
        dy = new_centroid[1] - self.centroid[1]
        step_movement = np.sqrt(dx * dx + dy * dy)
        self.total_movement += step_movement

        self.bbox = bbox
        self.centroid = new_centroid
        self.last_seen_seconds = timestamp
        self.total_visible_seconds += frame_interval_seconds
        self.frames_visible += 1
        self.disappeared_frames = 0
        self.is_active = True
        self.last_timestamp = timestamp

    def mark_missed(self, max_disappeared: int = 30):
        """Increment missed frame count and check if track exceeded retention threshold."""
        self.disappeared_frames += 1
        if self.disappeared_frames > max_disappeared:
            self.is_active = False

class ParticipantTracker:
    """
    Centroid and IoU based multi-object tracker for classroom attendees.
    Maintains track consistency across occlusions and momentary missed detections.
    """
    def __init__(self, max_disappeared_frames: int = 30, iou_threshold: float = 0.25, max_centroid_dist: float = 90.0):
        self.next_track_id = 1
        self.active_tracks: Dict[int, TrackRecord] = {}
        self.all_completed_tracks: Dict[int, TrackRecord] = {}
        self.max_disappeared_frames = max_disappeared_frames
        self.iou_threshold = iou_threshold
        self.max_centroid_dist = max_centroid_dist

    @staticmethod
    def compute_iou(boxA: Tuple[int, int, int, int], boxB: Tuple[int, int, int, int]) -> float:
        """Compute Intersection over Union between two bounding boxes (x, y, w, h)."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
        yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = boxA[2] * boxA[3]
        boxBArea = boxB[2] * boxB[3]
        unionArea = boxAArea + boxBArea - interArea

        if unionArea == 0:
            return 0.0
        return float(interArea / unionArea)

    def update(self, detections: List[Tuple[int, int, int, int]], timestamp: float, 
               frame_interval_seconds: float = 0.033) -> List[TrackRecord]:
        """
        Match incoming bounding boxes with existing tracks using IoU and Centroid distance.
        Returns list of currently active track records.
        """
        # If no detections in current frame, mark all active tracks as missed
        if len(detections) == 0:
            for tid, track in list(self.active_tracks.items()):
                track.mark_missed(self.max_disappeared_frames)
                if not track.is_active:
                    self.all_completed_tracks[tid] = track
                    del self.active_tracks[tid]
            return list(self.active_tracks.values())

        # If no active tracks currently, register all detections as new tracks
        if len(self.active_tracks) == 0:
            for bbox in detections:
                self._register_track(bbox, timestamp)
            return list(self.active_tracks.values())

        # Step 1: Compute IoU cost matrix
        active_tids = list(self.active_tracks.keys())
        active_records = [self.active_tracks[tid] for tid in active_tids]

        iou_matrix = np.zeros((len(active_records), len(detections)), dtype=np.float32)
        for i, track in enumerate(active_records):
            for j, bbox in enumerate(detections):
                iou_matrix[i, j] = self.compute_iou(track.bbox, bbox)

        assigned_tracks = set()
        assigned_detections = set()

        # Match by highest IoU above threshold
        while True:
            if iou_matrix.size == 0:
                break
            max_idx = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
            max_val = iou_matrix[max_idx]
            if max_val < self.iou_threshold:
                break
            i, j = max_idx
            track = active_records[i]
            track.update(detections[j], timestamp, frame_interval_seconds)
            assigned_tracks.add(track.track_id)
            assigned_detections.add(j)
            iou_matrix[i, :] = -1.0
            iou_matrix[:, j] = -1.0

        # Step 2: Centroid distance matching for remaining unassigned detections/tracks
        unassigned_track_indices = [i for i, t in enumerate(active_records) if t.track_id not in assigned_tracks]
        unassigned_detection_indices = [j for j in range(len(detections)) if j not in assigned_detections]

        for i in unassigned_track_indices:
            track = active_records[i]
            best_j = None
            best_dist = float("inf")
            for j in unassigned_detection_indices:
                det_box = detections[j]
                det_center = (det_box[0] + det_box[2] / 2.0, det_box[1] + det_box[3] / 2.0)
                dist = np.hypot(track.centroid[0] - det_center[0], track.centroid[1] - det_center[1])
                if dist < best_dist and dist < self.max_centroid_dist:
                    best_dist = dist
                    best_j = j
            if best_j is not None:
                track.update(detections[best_j], timestamp, frame_interval_seconds)
                assigned_tracks.add(track.track_id)
                assigned_detections.add(best_j)
                unassigned_detection_indices.remove(best_j)

        # Step 3: Handle unmatched tracks (mark missed)
        for track in active_records:
            if track.track_id not in assigned_tracks:
                track.mark_missed(self.max_disappeared_frames)
                if not track.is_active:
                    self.all_completed_tracks[track.track_id] = track
                    del self.active_tracks[track.track_id]

        # Step 4: Register remaining unassigned detections as new tracks
        for j in range(len(detections)):
            if j not in assigned_detections:
                self._register_track(detections[j], timestamp)

        return list(self.active_tracks.values())

    def _register_track(self, bbox: Tuple[int, int, int, int], timestamp: float):
        """Create and store a newly observed participant track."""
        track = TrackRecord(self.next_track_id, bbox, timestamp)
        self.active_tracks[self.next_track_id] = track
        self.next_track_id += 1

    def get_all_records(self) -> List[TrackRecord]:
        """Consolidate both active and completed tracks."""
        combined = dict(self.all_completed_tracks)
        combined.update(self.active_tracks)
        return list(combined.values())
