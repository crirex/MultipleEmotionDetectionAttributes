import cv2
import dlib
import numpy as np
from PySide6.QtCore import QObject
from imutils import face_utils
from scipy.ndimage import zoom
from scipy.spatial import distance

from PIL import Image

# from PySide6.QtWidgets import QMessageBox
from emotion_recognition.FaceEmotionDetectionThread import FaceEmotionDetectionThread
from reports import DataStoreManager
from utils.Logger import Logger
from utils.Manager import Manager
from utils.Timer import Timer


def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear


def is_face_detected(face):
    return face.shape[0] != 0 and face.shape[1] != 0


def get_representative_frame(frame_to_predictions, selected_class):
    frame_to_return = None
    max_accuracy = 0
    for frame, predictions in frame_to_predictions:
        accuracy = predictions[selected_class]
        if accuracy > max_accuracy:
            max_accuracy = accuracy
            frame_to_return = frame

    return frame_to_return


class FaceDetectionThread(QObject):
    def __init__(self, parent=None):
        super().__init__()
        self._calling_window = parent
        self._is_running = False
        self._is_paused = False
        self._abort = False
        self._logger = Logger()

        self._shape_x = 48
        self._shape_y = 48

        self._ear_thresh = 0.17
        self._no_classes = 7
        self._classes = {0: 'Angry', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 4: 'Sad', 5: 'Surprise', 6: 'Neutral'}

        self._nose_bridge = [28, 29, 30, 31, 33, 34, 35]
        self._face_detect = dlib.get_frontal_face_detector()

        self._videoTextFont = cv2.QT_FONT_NORMAL
        self._videoTextFontScale = 0.5
        self._videoTextColor = (255, 255, 255)
        self._facialRectangleColor = (0, 255, 0)
        self._facialDotsColor = (0, 0, 255)
        self._videoTextThickness = 0

        self.FACIAL_LANDMARKS_LEFT_EYE = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        self.FACIAL_LANDMARKS_RIGHT_EYE = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
        self.FACIAL_LANDMARKS_LEFT_EYEBROW = face_utils.FACIAL_LANDMARKS_IDXS["left_eyebrow"]
        self.FACIAL_LANDMARKS_RIGHT_EYEBROW = face_utils.FACIAL_LANDMARKS_IDXS["right_eyebrow"]
        self.FACIAL_LANDMARKS_NOSE = face_utils.FACIAL_LANDMARKS_IDXS["nose"]
        self.FACIAL_LANDMARKS_MOUTH = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]
        self.FACIAL_LANDMARKS_JAW = face_utils.FACIAL_LANDMARKS_IDXS["jaw"]

        self._frames = []

        self._manager = Manager()
        self._data_store_manager = DataStoreManager()

        self.video_prediction = FaceEmotionDetectionThread()

    def get_label(self, argument):
        return self._classes.get(argument, "Invalid emotion")

    def stop_running(self):
        self._is_running = self._is_paused = False

    def pause_running(self):
        self._is_paused = True

    def resume_running(self):
        self._is_paused = False

    def get_frame(self):
        if len(self._frames) > 0:
            return self._frames.pop(0)
        return None

    def has_glasses(self, shape, frame):
        landmarks = np.array([[p.x, p.y] for p in shape.parts()])

        nose_bridge_x = []
        nose_bridge_y = []

        for i in self._nose_bridge:
            nose_bridge_x.append(landmarks[i][0])
            nose_bridge_y.append(landmarks[i][1])

        # x_min and x_max
        x_min = min(nose_bridge_x)
        x_max = max(nose_bridge_x)

        # ymin (from top eyebrow coordinate),  ymax
        y_min = landmarks[20][1]
        y_max = landmarks[30][1]

        img2 = Image.fromarray(frame.astype(np.uint8))
        img2 = img2.crop((x_min, y_min, x_max, y_max))

        img_blur = cv2.GaussianBlur(np.array(img2), (3, 3), sigmaX=0, sigmaY=0)

        edges = cv2.Canny(image=img_blur, threshold1=100, threshold2=200)

        edges_center = edges.T[(int(len(edges.T) / 2))]

        if 255 in edges_center:
            return True

        return False

    def draw_face_dots(self, frame, shape):
        for (j, k) in shape:
            cv2.circle(img=frame, center=(j, k), radius=1, color=self._facialDotsColor, thickness=-1)

    def draw_rectangle(self, frame, x, y, width, height):
        cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)
        cv2.putText(img=frame, text="Face", org=(x - 10, y - 10),
                    fontFace=self._videoTextFont, fontScale=self._videoTextFontScale, color=(0, 255, 0),
                    thickness=self._videoTextThickness)

    def draw_main_prediction(self, frame, prediction, x, y, width):
        prediction_result = np.argmax(prediction)
        predictedLabelPosition = (x + width - 10, y - 10)
        if prediction_result == 0:
            cv2.putText(img=frame, text="Angry", org=predictedLabelPosition,
                        fontFace=self._videoTextFont, fontScale=1, color=self._facialRectangleColor, thickness=2)
        elif prediction_result == 1:
            cv2.putText(img=frame, text="Disgust", org=predictedLabelPosition,
                        fontFace=self._videoTextFont, fontScale=1, color=self._facialRectangleColor, thickness=2)
        elif prediction_result == 2:
            cv2.putText(img=frame, text="Fear", org=predictedLabelPosition,
                        fontFace=self._videoTextFont, fontScale=1, color=self._facialRectangleColor, thickness=2)
        elif prediction_result == 3:
            cv2.putText(img=frame, text="Happy", org=predictedLabelPosition,
                        fontFace=self._videoTextFont, fontScale=1, color=self._facialRectangleColor, thickness=2)
        elif prediction_result == 4:
            cv2.putText(img=frame, text="Sad", org=predictedLabelPosition,
                        fontFace=self._videoTextFont, fontScale=1, color=self._facialRectangleColor, thickness=2)
        elif prediction_result == 5:
            cv2.putText(img=frame, text="Surprise", org=predictedLabelPosition,
                        fontFace=self._videoTextFont, fontScale=1, color=self._facialRectangleColor, thickness=2)
        else:
            cv2.putText(img=frame, text="Neutral", org=predictedLabelPosition,
                        fontFace=self._videoTextFont, fontScale=1, color=self._facialRectangleColor, thickness=2)

    def draw_predictions(self, frame, prediction):
        cv2.putText(img=frame, text="Emotional report:",
                    org=(40, 120), fontFace=self._videoTextFont,
                    fontScale=self._videoTextFontScale, color=self._videoTextColor,
                    thickness=self._videoTextThickness)
        cv2.putText(img=frame, text="Angry : {}%".format(str(round(prediction[0][0] * 100, 2))),
                    org=(40, 140), fontFace=self._videoTextFont,
                    fontScale=self._videoTextFontScale, color=self._videoTextColor,
                    thickness=self._videoTextThickness)
        cv2.putText(img=frame, text="Disgust : {}%".format(str(round(prediction[0][1] * 100, 2))),
                    org=(40, 160), fontFace=self._videoTextFont,
                    fontScale=self._videoTextFontScale, color=self._videoTextColor,
                    thickness=self._videoTextThickness)
        cv2.putText(img=frame, text="Fear : {}%".format(str(round(prediction[0][2] * 100, 2))),
                    org=(40, 180), fontFace=self._videoTextFont,
                    fontScale=self._videoTextFontScale, color=self._videoTextColor,
                    thickness=self._videoTextThickness)
        cv2.putText(img=frame, text="Happy : {}%".format(str(round(prediction[0][3] * 100, 2))),
                    org=(40, 200), fontFace=self._videoTextFont,
                    fontScale=self._videoTextFontScale, color=self._videoTextColor,
                    thickness=self._videoTextThickness)
        cv2.putText(img=frame, text="Sad : {}%".format(str(round(prediction[0][4] * 100, 2))),
                    org=(40, 220), fontFace=self._videoTextFont,
                    fontScale=self._videoTextFontScale, color=self._videoTextColor,
                    thickness=self._videoTextThickness)
        cv2.putText(img=frame, text="Surprise : {}%".format(str(round(prediction[0][5] * 100, 2))),
                    org=(40, 240), fontFace=self._videoTextFont,
                    fontScale=self._videoTextFontScale, color=self._videoTextColor,
                    thickness=self._videoTextThickness)
        cv2.putText(img=frame, text="Neutral : {}%".format(str(round(prediction[0][6] * 100, 2))),
                    org=(40, 260), fontFace=self._videoTextFont,
                    fontScale=self._videoTextFontScale, color=self._videoTextColor,
                    thickness=self._videoTextThickness)

    def draw_if_open_eyes(self, frame, shape):
        (lStart, lEnd) = self.FACIAL_LANDMARKS_LEFT_EYE
        (rStart, rEnd) = self.FACIAL_LANDMARKS_RIGHT_EYE
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        ear = (leftEAR + rightEAR) / 2.0
        cv2.putText(img=frame, text="Eyes {}".format("Closed" if ear < self._ear_thresh else "Opened"),
                    org=(40, 400), fontFace=self._videoTextFont, fontScale=self._videoTextFontScale,
                    color=self._videoTextColor, thickness=self._videoTextThickness)

    def draw_if_glasses(self, frame, shape_img, gray):
        has_glasses = str(self.has_glasses(shape_img, gray))
        cv2.putText(img=frame, text="Glasses: {}".format(has_glasses),
                    org=(40, 380), fontFace=self._videoTextFont, fontScale=self._videoTextFontScale,
                    color=self._videoTextColor, thickness=self._videoTextThickness)

    def draw_eyes(self, frame, shape):
        (lStart, lEnd) = self.FACIAL_LANDMARKS_LEFT_EYE
        (rStart, rEnd) = self.FACIAL_LANDMARKS_RIGHT_EYE
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        leftEyeHull = cv2.convexHull(leftEye)
        rightEyeHull = cv2.convexHull(rightEye)
        cv2.drawContours(image=frame, contours=[leftEyeHull], contourIdx=-1,
                         color=(0, 255, 0), thickness=1)
        cv2.drawContours(image=frame, contours=[rightEyeHull], contourIdx=-1,
                         color=(0, 255, 0), thickness=1)

    def draw_nose(self, frame, shape):
        (nStart, nEnd) = self.FACIAL_LANDMARKS_NOSE
        nose = shape[nStart:nEnd]
        noseHull = cv2.convexHull(nose)
        cv2.drawContours(image=frame, contours=[noseHull], contourIdx=-1, color=(0, 255, 0), thickness=1)

    def draw_mouth(self, frame, shape):
        (mStart, mEnd) = self.FACIAL_LANDMARKS_MOUTH
        mouth = shape[mStart:mEnd]
        mouthHull = cv2.convexHull(mouth)
        cv2.drawContours(image=frame, contours=[mouthHull], contourIdx=-1, color=(0, 255, 0), thickness=1)

    def draw_jaw(self, frame, shape):
        (jStart, jEnd) = self.FACIAL_LANDMARKS_JAW
        jaw = shape[jStart:jEnd]
        jawHull = cv2.convexHull(jaw)
        cv2.drawContours(image=frame, contours=[jawHull], contourIdx=-1, color=(0, 255, 0), thickness=1)

    def draw_eyebrows(self, frame, shape):
        (eblStart, eblEnd) = self.FACIAL_LANDMARKS_LEFT_EYEBROW
        (ebrStart, ebrEnd) = self.FACIAL_LANDMARKS_RIGHT_EYEBROW
        ebl = shape[eblStart:eblEnd]
        ebr = shape[ebrStart:ebrEnd]
        eblHull = cv2.convexHull(ebl)
        ebrHull = cv2.convexHull(ebr)
        cv2.drawContours(image=frame, contours=[eblHull], contourIdx=-1, color=(0, 255, 0), thickness=1)
        cv2.drawContours(image=frame, contours=[ebrHull], contourIdx=-1, color=(0, 255, 0), thickness=1)

    def work(self):
        if not self._manager.is_camera_available():
            # QMessageBox.warning(self._calling_window, "Video", "There is no video input device available.")
            self._calling_window.ui.labelVideo.setText("No camera detected")
            return

        self._is_running = True
        self._is_paused = False
        self._abort = False

        predictions_map = {}
        frame_to_predictions = []
        timer = Timer()
        timer.start()
        start_time = timer.record_time()
        target_time = 4 * 1000
        try:
            while self._is_running:
                _, frame = self._manager.active_camera.read()

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                rects = self._face_detect(gray, 0)

                if len(predictions_map) == 0:
                    start_time = timer.record_time()

                current_time = timer.record_time()
                seconds_passed = current_time - start_time
                seconds = timer.record_time()
                if seconds_passed > target_time and len(predictions_map) > 0:
                    max_prediction = max(predictions_map, key=predictions_map.get)
                    print(f"Video prediction: {max_prediction}")
                    highest_class_index = [k for k, v in self._classes.items() if v == max_prediction][0]
                    representative_frame = get_representative_frame(frame_to_predictions, highest_class_index)
                    self._data_store_manager.insert_video((seconds, (representative_frame, max_prediction)))

                    predictions_map.clear()
                    frame_to_predictions.clear()
                    start_time = timer.record_time()

                if len(rects) and (not self._is_paused or len(predictions_map) > 0):
                    shape_img = self._manager.video_predictor_landmarks(gray, rects[0])
                    shape = face_utils.shape_to_np(shape_img)

                    (x, y, width, height) = face_utils.rect_to_bb(rects[0])
                    face = gray[y:y + height, x:x + width]

                    if is_face_detected(face):
                        # Zoom on extracted face
                        face = zoom(face, (self._shape_x / face.shape[0], self._shape_y / face.shape[1]))

                        # Cast type float
                        face = face.astype(np.float32)

                        # Scale
                        face /= float(face.max(initial=None))
                        face = np.reshape(face.flatten(), (1, 48, 48, 1))

                        self.video_prediction.queue_data(face)
                        prediction = self._manager.video_model.predict(face)
                        if prediction is None:
                            continue

                        frame_to_predictions.append((frame, prediction[0]))
                        prediction_emotion = self.get_label(np.argmax(prediction[0]))
                        predictions_map[prediction_emotion] = predictions_map[prediction_emotion] + 1 \
                            if prediction_emotion in predictions_map else 1

                        self.draw_predictions(frame, prediction)
                        self.draw_rectangle(frame, x, y, width, height)
                        self.draw_main_prediction(frame, prediction, x, y, width)
                        self.draw_if_open_eyes(frame, shape)
                        self.draw_if_glasses(frame, shape_img, gray)
                        self.draw_eyes(frame, shape)
                        self.draw_nose(frame, shape)
                        self.draw_mouth(frame, shape)
                        self.draw_jaw(frame, shape)
                        self.draw_eyebrows(frame, shape)
                        self.draw_face_dots(frame, shape)

                self._frames.append(frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            timer.stop()
        except Exception as ex:
            self._logger.log_error(ex)
            self._is_running = False
            self._manager.active_camera.release()
            raise Exception(ex)
        finally:
            self._frames.clear()
            self.video_prediction.abort()

    def abort(self):
        self._abort = True
        self._is_running = False
