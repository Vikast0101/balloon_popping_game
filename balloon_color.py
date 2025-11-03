import cv2
import random
import numpy as np
import HandTrackingModule as htm
import time

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

# Initialize game window
cap = cv2.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

# Balloon properties
balloons = []
for _ in range(num_balloons):
    x = random.randint(0, width - balloon_width)  # Random x position within bounds
    y = height + random.randint(0, 100)  # Start off-screen
    speed = random.randint(1, 5)  # Random upward speed
    start_time = time.time() + random.randint(0, 5)  # Random delay before balloon starts
    image = random.choice(balloon_images)  # Randomly select a balloon image
    balloons.append({'pos': [x, y], 'speed': speed, 'popped': False, 'start_time': start_time, 'image': image})

# Game variables
score = 0
balloons_passed = 0

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

        # Draw the index finger tip
        cv2.circle(img, (x_index, y_index), 10, (255, 0, 0), cv2.FILLED)

    # Update balloon positions and check for popping
    current_time = time.time()
    for balloon in balloons:
        # Only move the balloon if its start time has passed
        if current_time >= balloon['start_time'] and not balloon['popped']:
            # Move the balloon upward
            balloon['pos'][1] -= balloon['speed']

            # Check if the balloon has reached the top
            if balloon['pos'][1] < 0:
                balloon['popped'] = True  # Mark as "missed"
                balloons_passed += 1
                
            # Check for collision with index finger near the top of the balloon
            if len(lmList) != 0:
                # Adjust the collision detection to be around the top part of the balloon
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

    # Display the game frame
    cv2.imshow("Balloon Popping Game", img)

    # Check if all balloons have passed
    if balloons_passed >= num_balloons:
        cv2.putText(img, 'Game Over! Final Score:', (50, height // 2 - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(img, f'{score}', (width // 2 - 10, height // 2 + 30), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        cv2.imshow("Balloon Popping Game", img)
        cv2.waitKey(3000)  # Display final score for 3 seconds
        break

    # Exit the game when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()