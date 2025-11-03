from flask import Flask, render_template, Response, redirect, url_for
import cv2
import random
import numpy as np
import time
import HandTrackingModule as htm

app = Flask(__name__)

# Initialize the hand detector
detector = htm.handDetector(detectionCon=0.7)

# Game settings
width, height = 1000, 800  # Width and height of the game window
num_balloons = 40  # Set number of balloons to fly through the screen
balloon_width = 50  # Width of the balloon image
balloon_height = 150  # Height of the balloon image to make it taller

# Load multiple balloon images with transparent backgrounds
balloon_images = [
    cv2.resize(cv2.imread(f"balloon{i}.png", cv2.IMREAD_UNCHANGED), (balloon_width, balloon_height))
    for i in range(1, 6)
]

# Balloon properties
def initialize_game():
    global balloons, score, balloons_passed
    balloons = []
    for _ in range(num_balloons):
        x = random.randint(0, width - balloon_width)  # Random x position within bounds
        y = height + random.randint(0, 100)  # Start off-screen
        speed = random.randint(1, 5)  # Random upward speed
        start_time = time.time() + random.randint(0, 5)  # Random delay before balloon starts
        image = random.choice(balloon_images)  # Randomly select a balloon image
        balloons.append({'pos': [x, y], 'speed': speed, 'popped': False, 'start_time': start_time, 'image': image})

    # Reset game variables
    score = 0
    balloons_passed = 0

initialize_game()  # Initial game setup

def overlay_transparent(background, overlay, x, y):
    """Overlay an RGBA image (overlay) on the background at position (x, y)."""
    h, w = overlay.shape[:2]
    if x >= background.shape[1] or y >= background.shape[0]:
        return background

    # Compute region of interest
    y1, y2 = max(0, y), min(y + h, background.shape[0])
    x1, x2 = max(0, x), min(x + w, background.shape[1])

    # Adjust overlay and alpha to fit within region
    overlay_crop = overlay[0:y2 - y1, 0:x2 - x1]
    if overlay_crop.shape[2] == 4:  # Check if overlay has an alpha channel
        alpha_overlay = overlay_crop[:, :, 3] / 255.0
        alpha_background = 1.0 - alpha_overlay

        for c in range(3):  # For each color channel
            background[y1:y2, x1:x2, c] = (
                alpha_overlay * overlay_crop[:, :, c] +
                alpha_background * background[y1:y2, x1:x2, c]
            )
    return background

def generate_frames():
    global score, balloons_passed

    # Capture video from webcam
    cap = cv2.VideoCapture(0)
    cap.set(3, width)
    cap.set(4, height)

    while True:
        success, img = cap.read()
        if not success:
            break

        # Flip the camera feed horizontally
        img = cv2.flip(img, 1)

        # Find the hand and detect the index finger tip
        img = detector.findHands(img)
        lmList = detector.findPosition(img, draw=False)

        # Check if index finger tip is detected
        if len(lmList) != 0:
            x_index, y_index = lmList[8][1], lmList[8][2]  # Coordinates of the index fingertip

        # Update balloon positions and check for popping
        current_time = time.time()
        for balloon in balloons:
            if current_time >= balloon['start_time'] and not balloon['popped']:
                balloon['pos'][1] -= balloon['speed']

                # Check if the balloon has reached the top
                if balloon['pos'][1] < 0:
                    balloon['popped'] = True  # Mark as "missed"
                    balloons_passed += 1

                # Check for collision with index finger near the top of the balloon
                if len(lmList) != 0:
                    top_x, top_y = balloon['pos'][0] + balloon_width // 2, balloon['pos'][1] + balloon_height // 4
                    dist = np.hypot(x_index - top_x, y_index - top_y)
                    if dist < balloon_width // 2:  # Collision threshold based on balloon width
                        balloon['popped'] = True  # Mark as popped
                        score += 1
                        balloons_passed += 1

                # Draw the balloon if it hasn't been popped
                if not balloon['popped']:
                    img = overlay_transparent(img, balloon['image'], balloon['pos'][0], balloon['pos'][1])

        # Display score
        cv2.putText(img, f'Score: {score}', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img, f'Balloons Left: {num_balloons - balloons_passed}', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Convert to JPEG format
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
    cv2.destroyAllWindows()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/reset')
def reset():
    initialize_game()  # Reset the game state
    return redirect(url_for('index'))  # Redirect back to the main page

if __name__ == "__main__":
    app.run(debug=True)
