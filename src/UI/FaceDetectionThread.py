import numpy as np
from scipy.ndimage import zoom
from scipy.spatial import distance
import dlib
from tensorflow.keras.models import load_model
from imutils import face_utils
import cv2
from PySide6.QtCore import QThread


class FaceDetectionThread(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)

        self.is_running = True

        self.shape_x = 48
        self.shape_y = 48
        self.input_shape = (self.shape_x, self.shape_y, 1)
        self.nClasses = 7
        self.model = load_model('Models/video.h5')
        self.frames = []

    def stop_running(self):
        self.is_running = False

    def get_frame(self):
        if len(self.frames) > 0:
            return self.frames.pop(0)
        return None

    def eye_aspect_ratio(self, eye):
        A = distance.euclidean(eye[1], eye[5])
        B = distance.euclidean(eye[2], eye[4])
        C = distance.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def detect_face(self, frame):

        # Cascade classifier pre-trained model
        cascPath = 'Models/face_landmarks.dat'
        faceCascade = cv2.CascadeClassifier(cascPath)

        # BGR -> Gray conversion
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Cascade MultiScale classifier
        detected_faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6,
                                                      minSize=(self.shape_x, self.shape_y),
                                                      flags=cv2.CASCADE_SCALE_IMAGE)
        coord = []

        for x, y, w, h in detected_faces:
            if w > 100:
                sub_img = frame[y:y + h, x:x + w]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 1)
                coord.append([x, y, w, h])

        return gray, detected_faces, coord

    def extract_face_features(self, faces, offset_coefficients=(0.075, 0.05)):
        gray = faces[0]
        detected_face = faces[1]

        new_face = []

        for det in detected_face:
            # Region dans laquelle la face est détectée
            x, y, w, h = det
            # X et y correspondent à la conversion en gris par gray, et w, h correspondent à la hauteur/largeur

            # Offset coefficient, np.floor takes the lowest integer (delete border of the image)
            horizontal_offset = np.int(np.floor(offset_coefficients[0] * w))
            vertical_offset = np.int(np.floor(offset_coefficients[1] * h))

            # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # gray transforme l'image
            extracted_face = gray[y + vertical_offset:y + h, x + horizontal_offset:x - horizontal_offset + w]

            # Zoom sur la face extraite
            new_extracted_face = zoom(extracted_face,
                                      (self.shape_x / extracted_face.shape[0], self.shape_y / extracted_face.shape[1]))
            # cast type float
            new_extracted_face = new_extracted_face.astype(np.float32)
            # scale
            new_extracted_face /= float(new_extracted_face.max())
            # print(new_extracted_face)

            new_face.append(new_extracted_face)

        return new_face

    def run(self):

        self.is_running = True

        (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

        (nStart, nEnd) = face_utils.FACIAL_LANDMARKS_IDXS["nose"]
        (mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]
        (jStart, jEnd) = face_utils.FACIAL_LANDMARKS_IDXS["jaw"]

        (eblStart, eblEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eyebrow"]
        (ebrStart, ebrEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eyebrow"]

        face_detect = dlib.get_frontal_face_detector()
        predictor_landmarks = dlib.shape_predictor("Models/face_landmarks.dat")

        # Lancer la capture video
        video_capture = cv2.VideoCapture(0)

        while self.is_running:
            # Capture frame-by-frame
            ret, frame = video_capture.read()

            face_index = 0

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rects = face_detect(gray, 0)
            # gray, detected_faces, coord = detect_face(frame)

            for (i, rect) in enumerate(rects):

                shape = predictor_landmarks(gray, rect)
                shape = face_utils.shape_to_np(shape)

                # Identify face coordinates
                (x, y, w, h) = face_utils.rect_to_bb(rect)
                face = gray[y:y + h, x:x + w]

                if face.shape[0] == 0 or face.shape[1] == 0:
                    continue

                # Zoom on extracted face
                face = zoom(face, (self.shape_x / face.shape[0], self.shape_y / face.shape[1]))

                # Cast type float
                face = face.astype(np.float32)

                # Scale
                face /= float(face.max())
                face = np.reshape(face.flatten(), (1, 48, 48, 1))

                # Make Prediction
                prediction = self.model.predict(face)
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
                leftEAR = self.eye_aspect_ratio(leftEye)
                rightEAR = self.eye_aspect_ratio(rightEye)
                ear = (leftEAR + rightEAR) / 2.0

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

            print("Inside facedectionthread")
            self.frames.append(frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        print("Outside facedetectionthread")
        # When everything is done, release the capture
        video_capture.release()
        cv2.destroyAllWindows()
