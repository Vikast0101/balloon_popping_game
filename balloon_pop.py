import cv2
import random
import numpy as np
import HandTrackingModule as htm
import math
import time

# Initialize the hand detector
detector = htm.handDetector(detectionCon=0.7)

# Game settings
width, height = 800, 600  # Width and height of the game window
num_balloons = 40  # Set number of balloons to fly through the screen
balloon_size = 25  # Size of the balloon

# Initialize game window
cap = cv2.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

# Balloon properties
balloons = []
for _ in range(num_balloons):
    x = random.randint(0, width)  # Random x position
    y = height + random.randint(0, 100)  # Start off-screen
    speed = random.randint(1, 5)  # Random upward speed
    start_time = time.time() + random.randint(0, 5)  # Random delay before balloon starts
    balloons.append({'pos': [x, y], 'speed': speed, 'popped': False, 'start_time': start_time})

# Game variables
score = 0
balloons_passed = 0

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
                balloon['pos'][1] = height + random.randint(0, 100)  # Reset position to bottom
                balloon['popped'] = True  # Mark as "missed"
                balloons_passed += 1

            # Check for collision with index finger
            if len(lmList) != 0:
                dist = np.hypot(x_index - balloon['pos'][0], y_index - balloon['pos'][1])
                if dist < balloon_size:  # Collision threshold
                    balloon['popped'] = True  # Mark as popped
                    score += 1
                    balloons_passed += 1

            # Draw the balloon if it hasn't been popped
            if not balloon['popped']:
                cv2.circle(img, (balloon['pos'][0], balloon['pos'][1]), balloon_size, (0, 0, 255), -1)

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
