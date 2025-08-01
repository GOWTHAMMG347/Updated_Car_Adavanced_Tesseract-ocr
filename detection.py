import cv2
import os
import pytesseract
import shutil

CASCADE_PATH = "model/haarcascade_russian_plate_number.xml"
cascade = cv2.CascadeClassifier(CASCADE_PATH)

# Detect Tesseract path (works inside Docker)
tesseract_path = shutil.which("tesseract")
if not tesseract_path:
    print("⚠️ Tesseract not found! OCR will be disabled.")
else:
    print(f"🔎 Checking Tesseract installation...\nTesseract path: {tesseract_path}")

pytesseract.pytesseract.tesseract_cmd = tesseract_path or "tesseract"

webcam_running = False
webcam_cap = None
detected_plates = []

def extract_plate_text(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    try:
        return pytesseract.image_to_string(gray, config='--oem 3 --psm 7').strip()
    except pytesseract.TesseractNotFoundError:
        return ""

def blur_region(frame, x, y, w, h):
    roi = frame[y:y + h, x:x + w]
    frame[y:y + h, x:x + w] = cv2.GaussianBlur(roi, (51, 51), 30)
    return frame

def save_output_file(output_path, frame_list, is_video=False):
    if is_video:
        height, width, _ = frame_list[0].shape
        out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'XVID'), 20, (width, height))
        for frame in frame_list:
            out.write(frame)
        out.release()
    else:
        cv2.imwrite(output_path, frame_list)

def process_image(input_path, output_path):
    global detected_plates
    detected_plates = []
    image = cv2.imread(input_path)
    plates = cascade.detectMultiScale(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 1.1, 4)
    for (x, y, w, h) in plates:
        plate_text = extract_plate_text(image[y:y + h, x:x + w])
        if plate_text:
            detected_plates.append(plate_text)
        image = blur_region(image, x, y, w, h)
    cv2.imwrite(output_path, image)
    return detected_plates

def process_video(input_path, output_path):
    global detected_plates
    detected_plates = []
    cap = cv2.VideoCapture(input_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        plates = cascade.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 1.1, 4)
        for (x, y, w, h) in plates:
            plate_text = extract_plate_text(frame[y:y + h, x:x + w])
            if plate_text and plate_text not in detected_plates:
                detected_plates.append(plate_text)
            frame = blur_region(frame, x, y, w, h)
        frames.append(frame)
    cap.release()
    save_output_file(output_path, frames, is_video=True)
    return detected_plates

def start_webcam(frames_dir="static/frames"):
    global webcam_running, webcam_cap, detected_plates
    if not os.path.exists(frames_dir):
        os.makedirs(frames_dir)
    webcam_running = True
    webcam_cap = cv2.VideoCapture(0)
    detected_plates = []

def stop_webcam():
    global webcam_running, webcam_cap
    webcam_running = False
    if webcam_cap:
        webcam_cap.release()

def get_webcam_frame(frames_dir="static/frames"):
    global webcam_cap, webcam_running, detected_plates
    if not webcam_cap or not webcam_running:
        return None
    ret, frame = webcam_cap.read()
    if not ret:
        return None
    plates = cascade.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 1.1, 4)
    for (x, y, w, h) in plates:
        plate_text = extract_plate_text(frame[y:y + h, x:x + w])
        if plate_text and plate_text not in detected_plates:
            detected_plates.append(plate_text)
        frame = blur_region(frame, x, y, w, h)
    output_path = os.path.join(frames_dir, "live.jpg")
    cv2.imwrite(output_path, frame)
    return output_path

def get_detected_plates():
    return detected_plates
