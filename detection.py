import cv2
import os
import pytesseract
import shutil

# Haarcascade model path
CASCADE_PATH = "model/haarcascade_russian_plate_number.xml"
cascade = cv2.CascadeClassifier(CASCADE_PATH)

# Dynamically detect Tesseract path
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    print(f"✅ Tesseract found at: {tesseract_path}")
else:
    print("⚠️ Tesseract not found! OCR will be disabled.")

webcam_running = False
webcam_cap = None
detected_plates = []

# --- OCR Helper ---
def extract_plate_text(image):
    """
    Extracts text from a license plate image using Tesseract OCR.
    If Tesseract is missing, it will gracefully continue without OCR.
    """
    if not tesseract_path:
        return ""  # Skip OCR if Tesseract not available

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    try:
        text = pytesseract.image_to_string(gray, config='--oem 3 --psm 7')
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        print("⚠️ Tesseract not found! Continuing without OCR.")
        return ""

# --- Blur helper ---
def blur_region(frame, x, y, w, h):
    """
    Applies Gaussian blur to the detected license plate region.
    """
    roi = frame[y:y + h, x:x + w]
    blurred = cv2.GaussianBlur(roi, (51, 51), 30)
    frame[y:y + h, x:x + w] = blurred
    return frame

# --- Save processed outputs ---
def save_output_file(output_path, frame_list, is_video=False):
    """
    Saves processed frames as an image or a video.
    """
    if is_video:
        height, width, _ = frame_list[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_path, fourcc, 20, (width, height))
        for frame in frame_list:
            out.write(frame)
        out.release()
    else:
        cv2.imwrite(output_path, frame_list)

# --- Process image ---
def process_image(input_path, output_path):
    """
    Processes a single image: detects plates, blurs them, and extracts text.
    """
    global detected_plates
    detected_plates = []

    image = cv2.imread(input_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    plates = cascade.detectMultiScale(gray, 1.1, 4)

    for (x, y, w, h) in plates:
        plate_roi = image[y:y + h, x:x + w]
        plate_text = extract_plate_text(plate_roi)
        if plate_text:
            detected_plates.append(plate_text)
        image = blur_region(image, x, y, w, h)

    cv2.imwrite(output_path, image)
    return detected_plates

# --- Process video ---
def process_video(input_path, output_path):
    """
    Processes a video: detects plates, blurs them, and extracts text frame by frame.
    """
    global detected_plates
    detected_plates = []

    cap = cv2.VideoCapture(input_path)
    frames = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        plates = cascade.detectMultiScale(gray, 1.1, 4)

        for (x, y, w, h) in plates:
            plate_roi = frame[y:y + h, x:x + w]
            plate_text = extract_plate_text(plate_roi)
            if plate_text and plate_text not in detected_plates:
                detected_plates.append(plate_text)
            frame = blur_region(frame, x, y, w, h)

        frames.append(frame)

    cap.release()
    save_output_file(output_path, frames, is_video=True)
    return detected_plates

# --- Webcam control ---
def start_webcam(frames_dir="static/frames"):
    """
    Starts webcam capture and creates a frames directory if it doesn't exist.
    """
    global webcam_running, webcam_cap, detected_plates
    if not os.path.exists(frames_dir):
        os.makedirs(frames_dir)
    webcam_running = True
    webcam_cap = cv2.VideoCapture(0)
    detected_plates = []

def stop_webcam():
    """
    Stops webcam capture.
    """
    global webcam_running, webcam_cap
    webcam_running = False
    if webcam_cap:
        webcam_cap.release()

def get_webcam_frame(frames_dir="static/frames"):
    """
    Captures a single webcam frame, processes it for plate detection, 
    and saves it as 'live.jpg' in the frames directory.
    """
    global webcam_cap, webcam_running, detected_plates

    if not webcam_cap or not webcam_running:
        return None

    ret, frame = webcam_cap.read()
    if not ret:
        return None

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    plates = cascade.detectMultiScale(gray, 1.1, 4)

    for (x, y, w, h) in plates:
        plate_roi = frame[y:y + h, x:x + w]
        plate_text = extract_plate_text(plate_roi)
        if plate_text and plate_text not in detected_plates:
            detected_plates.append(plate_text)
        frame = blur_region(frame, x, y, w, h)

    output_path = os.path.join(frames_dir, "live.jpg")
    cv2.imwrite(output_path, frame)
    return output_path

def get_detected_plates():
    """
    Returns a list of all detected plate texts during the session.
    """
    return detected_plates
