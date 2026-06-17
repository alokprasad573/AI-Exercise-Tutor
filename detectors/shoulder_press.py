from core.base_exercise import BaseExercise
import math


class ShoulderPressDetector(BaseExercise):
    DOWN_THRESHOLD = 90
    UP_THRESHOLD = 150
    MIN_VISIBILITY = 0.7

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps = 0
        self.stage = None

    def process(self, landmarks) -> dict:
        left_vis = landmarks[self.LEFT_ELBOW].visibility
        right_vis = landmarks[self.RIGHT_ELBOW].visibility

        if left_vis >= right_vis:
            shoulder_idx = self.LEFT_SHOULDER
            elbow_idx = self.LEFT_ELBOW
            wrist_idx = self.LEFT_WRIST
            hip_idx = self.LEFT_HIP
        else:
            shoulder_idx = self.RIGHT_SHOULDER
            elbow_idx = self.RIGHT_ELBOW
            wrist_idx = self.RIGHT_WRIST
            hip_idx = self.RIGHT_HIP

        elbow_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, elbow_idx),
            self.get_point(landmarks, wrist_idx)
        )

        key_landmarks_visible = (
            landmarks[shoulder_idx].visibility > self.MIN_VISIBILITY
            and landmarks[elbow_idx].visibility > self.MIN_VISIBILITY
            and landmarks[wrist_idx].visibility > self.MIN_VISIBILITY
        )

        if key_landmarks_visible:
            if elbow_angle < self.DOWN_THRESHOLD:
                self.stage = "down"
            elif elbow_angle > self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        if elbow_angle > 160:
            extension_status = "FULL"
        elif elbow_angle > 140:
            extension_status = "PARTIAL"
        else:
            extension_status = "LOW"

        # Back arch check
        shoulder_x = landmarks[shoulder_idx].x
        shoulder_y = landmarks[shoulder_idx].y
        hip_x = landmarks[hip_idx].x
        hip_y = landmarks[hip_idx].y
        
        dx = shoulder_x - hip_x
        dy = shoulder_y - hip_y
        
        back_angle = math.degrees(math.atan2(abs(dx), abs(dy))) if dy != 0 else 0.0
        
        if back_angle > 15:
            back_arch_status = "ARCHED"
        else:
            back_arch_status = "GOOD"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "extension_status": extension_status,
            "back_arch_status": back_arch_status
        }
