import cv2
import dlib
import numpy as np

from scipy.ndimage import zoom
from scipy.spatial import distance
from imutils import face_utils
from PIL import Image
from PySide6.QtCore import QThread

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
        self.calling_window = parent
        self.is_running = True

        self.shape_x = 48
        self.shape_y = 48

        self.thresh = 0.17
        self.nClasses = 7

        self.nose_bridge = [28, 29, 30, 31, 33, 34, 35]
        self.manager = Manager()
        self.face_detect = dlib.get_frontal_face_detector()

        self.frames = []

    def stop_running(self):
        self.is_running = False

    def get_frame(self):
        if len(self.frames) > 0:
            return self.frames.pop(0)
        return None

    def detect_face(self, frame):

        # Cascade classifier pre-trained model
        faceCascade = cv2.CascadeClassifier('Models/face_landmarks.dat')

        # BGR -> Gray conversion
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Cascade MultiScale classifier
        detected_faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6,
                                                      minSize=(self.shape_x, self.shape_y),
                                                      flags=cv2.CASCADE_SCALE_IMAGE)
        coord = []

        for x, y, w, h in detected_faces:
            if w > 100:
                # sub_img = frame[y:y + h, x:x + w]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 1)
                coord.append([x, y, w, h])

        return gray, detected_faces, coord

    def has_glasses(self, shape, frame):
        landmarks = np.array([[p.x, p.y] for p in shape.parts()])

        nose_bridge_x = []
        nose_bridge_y = []

        for i in self.nose_bridge:
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

    def run(self):
        self.is_running = True

        (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

        (nStart, nEnd) = face_utils.FACIAL_LANDMARKS_IDXS["nose"]
        (mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]
        (jStart, jEnd) = face_utils.FACIAL_LANDMARKS_IDXS["jaw"]

        (eblStart, eblEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eyebrow"]
        (ebrStart, ebrEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eyebrow"]

        if self.manager.activeCamera is None or not self.manager.activeCamera.isOpened():
            self.calling_window.ui.labelVideo.setText("No camera detected")
            return

        while self.is_running:
            ret, frame = self.manager.activeCamera.read()

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rects = self.face_detect(gray, 0)

            for (i, rect) in enumerate(rects):

                shape_img = self.manager.videoPredictorLandmarks(gray, rect)
                shape = face_utils.shape_to_np(shape_img)

                (x, y, w, h) = face_utils.rect_to_bb(rect)
                face = gray[y:y + h, x:x + w]

                if not is_face_detected(face):
                    self.frames.append(frame)
                    continue

                # Zoom on extracted face
                face = zoom(face, (self.shape_x / face.shape[0], self.shape_y / face.shape[1]))

                # Cast type float
                face = face.astype(np.float32)

                # Scale
                face /= float(face.max())
                face = np.reshape(face.flatten(), (1, 48, 48, 1))

                # Make Prediction
                prediction = self.manager.videoModel.predict(face)
                prediction_result = np.argmax(prediction)

                # Rectangle around the face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cv2.putText(frame, "Face #{}".format(i + 1), (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 255, 0), 2)

                for (j, k) in shape:
                    cv2.circle(frame, (j, k), 1, (0, 0, 255), -1)

                # 1. Add prediction probabilities
                cv2.putText(frame, "----------------", (40, 100 + 180 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 155, 0)
                cv2.putText(frame, "Emotional report : Face #" + str(i + 1), (40, 120 + 180 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, 155, 0)
                cv2.putText(frame, "Angry : " + str(round(prediction[0][0], 3)), (40, 140 + 180 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, 155, 0)
                cv2.putText(frame, "Disgust : " + str(round(prediction[0][1], 3)), (40, 160 + 180 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, 155, 0)
                cv2.putText(frame, "Fear : " + str(round(prediction[0][2], 3)), (40, 180 + 180 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, 155, 1)
                cv2.putText(frame, "Happy : " + str(round(prediction[0][3], 3)), (40, 200 + 180 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, 155, 1)
                cv2.putText(frame, "Sad : " + str(round(prediction[0][4], 3)), (40, 220 + 180 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, 155, 1)
                cv2.putText(frame, "Surprise : " + str(round(prediction[0][5], 3)), (40, 240 + 180 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, 155, 1)
                cv2.putText(frame, "Neutral : " + str(round(prediction[0][6], 3)), (40, 260 + 180 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, 155, 1)

                # 2. Annotate main image with a label
                if prediction_result == 0:
                    cv2.putText(frame, "Angry", (x + w - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                elif prediction_result == 1:
                    cv2.putText(frame, "Disgust", (x + w - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                elif prediction_result == 2:
                    cv2.putText(frame, "Fear", (x + w - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                elif prediction_result == 3:
                    cv2.putText(frame, "Happy", (x + w - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                elif prediction_result == 4:
                    cv2.putText(frame, "Sad", (x + w - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                elif prediction_result == 5:
                    cv2.putText(frame, "Surprise", (x + w - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "Neutral", (x + w - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # 3. Eye Detection and Blink Count
                leftEye = shape[lStart:lEnd]
                rightEye = shape[rStart:rEnd]

                # Compute Eye Aspect Ratio
                leftEAR = eye_aspect_ratio(leftEye)
                rightEAR = eye_aspect_ratio(rightEye)
                ear = (leftEAR + rightEAR) / 2.0

                # Output Eye Detection Results
                cv2.putText(frame, "Eyes " + ("Closed" if ear < self.thresh else "Opened"), (40, 400),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, 155, 0)
                print("EAR: " + str(ear))

                # Output Glasses Detection
                has_glasses = str(self.has_glasses(shape_img, gray))
                cv2.putText(frame, "Glasses: " + has_glasses, (40, 380),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, 155, 1)
                print("Glasses: " + has_glasses)

                # And plot its contours
                leftEyeHull = cv2.convexHull(leftEye)
                rightEyeHull = cv2.convexHull(rightEye)
                cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

                # 4. Detect Nose
                nose = shape[nStart:nEnd]
                noseHull = cv2.convexHull(nose)
                cv2.drawContours(frame, [noseHull], -1, (0, 255, 0), 1)

                # 5. Detect Mouth
                mouth = shape[mStart:mEnd]
                mouthHull = cv2.convexHull(mouth)
                cv2.drawContours(frame, [mouthHull], -1, (0, 255, 0), 1)

                # 6. Detect Jaw
                jaw = shape[jStart:jEnd]
                jawHull = cv2.convexHull(jaw)
                cv2.drawContours(frame, [jawHull], -1, (0, 255, 0), 1)

                # 7. Detect Eyebrows
                ebr = shape[ebrStart:ebrEnd]
                ebrHull = cv2.convexHull(ebr)
                cv2.drawContours(frame, [ebrHull], -1, (0, 255, 0), 1)
                ebl = shape[eblStart:eblEnd]
                eblHull = cv2.convexHull(ebl)
                cv2.drawContours(frame, [eblHull], -1, (0, 255, 0), 1)

            cv2.putText(frame, 'Number of Faces : ' + str(len(rects)), (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, 155, 1)

            self.frames.append(frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # self.manager.activeCamera.release()
