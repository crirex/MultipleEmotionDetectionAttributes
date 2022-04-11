import cv2
import dlib
import numpy as np

from scipy.ndimage import zoom
from scipy.spatial import distance
from imutils import face_utils
from PIL import Image

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QThread

from utils.Logger import Logger
from utils.Manager import Manager


def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear


def is_face_detected(face):
    return face.shape[0] != 0 and face.shape[1] != 0


class FaceDetectionThread(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self._calling_window = parent
        self._is_running = True
        self._logger = Logger()

        self._shape_x = 48
        self._shape_y = 48

        self._ear_thresh = 0.17
        self._no_classes = 7

        self._nose_bridge = [28, 29, 30, 31, 33, 34, 35]
        self._manager = Manager()
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

    def stop_running(self):
        self._is_running = False

    def get_frame(self):
        if len(self._frames) > 0:
            return self._frames.pop(0)
        return None

    def detect_face(self, frame):

        # Cascade classifier pre-trained model
        faceCascade = cv2.CascadeClassifier('Models/face_landmarks.dat')

        # BGR -> Gray conversion
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Cascade MultiScale classifier
        detected_faces = faceCascade.detectMultiScale(image=gray, scaleFactor=1.1, minNeighbors=6,
                                                      minSize=(self._shape_x, self._shape_y),
                                                      flags=cv2.CASCADE_SCALE_IMAGE)
        coord = []

        for x, y, w, h in detected_faces:
            if w > 100:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 1)
                coord.append([x, y, w, h])

        return gray, detected_faces, coord

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

    def drawFaceDots(self, frame, shape):
        for (j, k) in shape:
            cv2.circle(img=frame, center=(j, k), radius=1, color=self._facialDotsColor, thickness=-1)

    def drawRectangle(self, frame, x, y, width, height):
        cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)
        cv2.putText(img=frame, text="Face", org=(x - 10, y - 10),
                    fontFace=self._videoTextFont, fontScale=self._videoTextFontScale, color=(0, 255, 0),
                    thickness=self._videoTextThickness)

    def drawMainPrediction(self, frame, prediction, x, y, width):
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

    def drawPredictions(self, frame, prediction):
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

    def drawIfOpenEyes(self, frame, shape):
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

    def drawIfGlasses(self, frame, shape_img, gray):
        has_glasses = str(self.has_glasses(shape_img, gray))
        cv2.putText(img=frame, text="Glasses: {}".format(has_glasses),
                    org=(40, 380), fontFace=self._videoTextFont, fontScale=self._videoTextFontScale,
                    color=self._videoTextColor, thickness=self._videoTextThickness)

    def drawEyes(self, frame, shape):
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

    def drawNose(self, frame, shape):
        (nStart, nEnd) = self.FACIAL_LANDMARKS_NOSE
        nose = shape[nStart:nEnd]
        noseHull = cv2.convexHull(nose)
        cv2.drawContours(image=frame, contours=[noseHull], contourIdx=-1, color=(0, 255, 0), thickness=1)

    def drawMouth(self, frame, shape):
        (mStart, mEnd) = self.FACIAL_LANDMARKS_MOUTH
        mouth = shape[mStart:mEnd]
        mouthHull = cv2.convexHull(mouth)
        cv2.drawContours(image=frame, contours=[mouthHull], contourIdx=-1, color=(0, 255, 0), thickness=1)

    def drawJaw(self, frame, shape):
        (jStart, jEnd) = self.FACIAL_LANDMARKS_JAW
        jaw = shape[jStart:jEnd]
        jawHull = cv2.convexHull(jaw)
        cv2.drawContours(image=frame, contours=[jawHull], contourIdx=-1, color=(0, 255, 0), thickness=1)

    def drawEyebrows(self, frame, shape):
        (eblStart, eblEnd) = self.FACIAL_LANDMARKS_LEFT_EYEBROW
        (ebrStart, ebrEnd) = self.FACIAL_LANDMARKS_RIGHT_EYEBROW
        ebl = shape[eblStart:eblEnd]
        ebr = shape[ebrStart:ebrEnd]
        eblHull = cv2.convexHull(ebl)
        ebrHull = cv2.convexHull(ebr)
        cv2.drawContours(image=frame, contours=[eblHull], contourIdx=-1, color=(0, 255, 0), thickness=1)
        cv2.drawContours(image=frame, contours=[ebrHull], contourIdx=-1, color=(0, 255, 0), thickness=1)

    def run(self):
        if self._manager.active_camera is None or not self._manager.active_camera.isOpened():
            QMessageBox.warning(None, "Video", "There is no video input device available.")
            self._calling_window.ui.labelVideo.setText("No camera detected")
            return

        self._is_running = True

        try:
            while self._is_running:
                _, frame = self._manager.active_camera.read()

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                rects = self._face_detect(gray, 0)

                if len(rects):
                    shape_img = self._manager.video_predictor_landmarks(gray, rects[0])
                    shape = face_utils.shape_to_np(shape_img)

                    (x, y, width, height) = face_utils.rect_to_bb(rects[0])
                    face = gray[y:y + height, x:x + width]

                    if not is_face_detected(face):
                        self._frames.append(frame)
                        continue

                    # Zoom on extracted face
                    face = zoom(face, (self._shape_x / face.shape[0], self._shape_y / face.shape[1]))

                    # Cast type float
                    face = face.astype(np.float32)

                    # Scale
                    face /= float(face.max())
                    face = np.reshape(face.flatten(), (1, 48, 48, 1))

                    # Make Prediction
                    prediction = self._manager.video_model.predict(face)

                    self.drawPredictions(frame, prediction)
                    self.drawRectangle(frame, x, y, width, height)
                    self.drawMainPrediction(frame, prediction, x, y, width)
                    self.drawIfOpenEyes(frame, shape)
                    self.drawIfGlasses(frame, shape_img, gray)
                    self.drawEyes(frame, shape)
                    self.drawNose(frame, shape)
                    self.drawMouth(frame, shape)
                    self.drawJaw(frame, shape)
                    self.drawEyebrows(frame, shape)
                    self.drawFaceDots(frame, shape)

                self._frames.append(frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        except Exception as ex:
            self._logger.log_error(ex)
            self._is_running = False
            self._manager.active_camera.release()
            raise Exception(ex)
