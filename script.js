// ===== DOM references =====
const video = document.getElementById("video");
const canvas = document.getElementById("output");
const ctx = canvas.getContext("2d");
const statusElement = document.getElementById("status");
const startBtn = document.getElementById("start-btn");
const gameOverDiv = document.getElementById("game-over");
const resultText = document.getElementById("result-text");
const playAgainBtn = document.getElementById("play-again-btn");
const instructionsDiv = document.getElementById("instructions");

// ===== Game state =====
let balloons = [];
let popped = 0;
let missed = 0;
let width, height;
const totalBalloons = 30;
let balloonCount = 0;
let gameStarted = false;
let spawnTimer = null;
let rafId = null;

// Audio
const popSound = new Audio("assets/pop.mp3");

// Hide canvas initially so instructions are visible
canvas.style.display = "none";

/**
 * Resize canvas to match its displayed size.
 * CSS controls width; we fit height to the camera aspect (closer to original 4:3).
 */
function resizeCanvas() {
  const cssWidth = canvas.clientWidth || Math.min(window.innerWidth * 0.75, 800);
  const aspect =
    (video && video.videoWidth && video.videoHeight)
      ? (video.videoHeight / video.videoWidth)
      : (3 / 4); // original-like 640x480 look
  const cssHeight = Math.min(cssWidth * aspect, window.innerHeight * 0.85);

  width = canvas.width = Math.floor(cssWidth);
  height = canvas.height = Math.floor(cssHeight);
}
resizeCanvas();
window.addEventListener("resize", resizeCanvas);

// ===== Assets for balloons =====
const balloonImages = [
  "assets/balloon1.png",
  "assets/balloon2.png",
  "assets/balloon3.png",
  "assets/balloon4.png",
  "assets/balloon5.png",
];
const loadedImages = [];
for (const src of balloonImages) {
  const img = new Image();
  img.src = src;
  loadedImages.push(img);
}

// ===== Balloons (same logic, slightly slower than original) =====
function createBalloon() {
  if (balloonCount >= totalBalloons) return;
  const img = loadedImages[Math.floor(Math.random() * loadedImages.length)];
  const scale = 0.5 + Math.random() * 0.5; // 50%–100%
  const w = 70 * scale;
  const h = 90 * scale;

  const b = {
    img,
    x: Math.random() * (width - w) + w / 2,
    y: height + h,         // start below canvas
    w,
    h,
    // ORIGINAL was ~1.0–2.5; make it a bit slower but same behavior:
    speed: 0.7 + Math.random() * 1.0, // 0.7–1.7 px/frame
    popped: false,
  };
  balloons.push(b);
  balloonCount++;
}

function updateBalloons() {
  for (const b of balloons) {
    if (!b.popped) {
      b.y -= b.speed;
      if (b.y + b.h * 0.5 < 0) {
        b.popped = true; // missed
        missed++;
      }
    }
  }
  // If you add burst/fade later, keep popped until alpha<=0; for now just filter
  balloons = balloons.filter(b => !b.popped || b.alpha > 0);
}

function drawBalloons() {
  for (const b of balloons) {
    if (!b.popped) {
      ctx.drawImage(b.img, b.x - b.w / 2, b.y - b.h / 2, b.w, b.h);
    }
  }
}

// ===== End & overlay =====
function endIfDone() {
  if (popped + missed >= totalBalloons) {
    gameStarted = false;
    stopSpawning();
    if (rafId) cancelAnimationFrame(rafId);

    resultText.textContent = `Game Over! You popped ${popped} / ${totalBalloons}.`;

    // Show the "game ended + play again" panel (works whether CSS uses .show or inline display)
    gameOverDiv.classList.add("show");
    gameOverDiv.style.display = "flex";
  }
}

// ===== MediaPipe Hands (same method as original) =====
const hands = new Hands({
  locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
});
hands.setOptions({
  maxNumHands: 1,
  modelComplexity: 1,
  minDetectionConfidence: 0.6,
  minTrackingConfidence: 0.6,
});
hands.onResults(onResults);

// ===== Render (same flow; we only add mirror + fingertip dot) =====
function onResults(results) {
  if (!gameStarted) return;

  // Draw MIRRORED live feed as background
  ctx.clearRect(0, 0, width, height);
  if (results.image) {
    try {
      ctx.save();
      ctx.scale(-1, 1);                 // mirror horizontally
      ctx.drawImage(results.image, -width, 0, width, height);
      ctx.restore();
    } catch (e) {}
  }

  // Balloons on top
  drawBalloons();

  // Index finger tip (same landmarks method; mirrored X to match view)
  if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
    const lm = results.multiHandLandmarks[0][8]; // index fingertip
    const fx = width - (lm.x * width);  // mirrored X
    const fy = lm.y * height;

    // Visible fingertip marker (no smoothing, original responsiveness)
    ctx.beginPath();
    ctx.arc(fx, fy, 10, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(0,150,255,0.9)";
    ctx.fill();

    // Collision
    for (const b of balloons) {
      if (b.popped) continue;
      const dx = fx - b.x;
      const dy = fy - b.y;
      const r = Math.min(b.w, b.h) * 0.4;
      if (dx * dx + dy * dy <= r * r) {
        b.popped = true;
        popped++;
        try { popSound.currentTime = 0; popSound.play(); } catch (e) {}
      }
    }
  }

  statusElement.textContent = `Popped: ${popped} / ${totalBalloons}`;
  endIfDone();
}

// ===== Camera (same onFrame method as original) =====
async function initCamera() {
  const stream = await navigator.mediaDevices.getUserMedia({ video: true });
  video.srcObject = stream;

  const camera = new Camera(video, {
    onFrame: async () => {
      if (gameStarted) {
        resizeCanvas();               // keep canvas sized to actual feed/container
        await hands.send({ image: video });
      }
    },
    width: 640,   // original-like dimensions
    height: 480,
  });
  camera.start();

  video.onloadedmetadata = () => resizeCanvas();
}

// ===== Game loop (original style; no dt scaling) =====
function loop() {
  if (!gameStarted) return;
  updateBalloons();
  rafId = requestAnimationFrame(loop);
}

// ===== Spawning cadence (original feel) =====
function startSpawning() {
  stopSpawning();
  spawnTimer = setInterval(() => {
    if (balloonCount < totalBalloons) {
      createBalloon();
    } else {
      stopSpawning();
    }
  }, 700);
}
function stopSpawning() {
  if (spawnTimer) {
    clearInterval(spawnTimer);
    spawnTimer = null;
  }
}

// ===== Controls =====
function resetGame() {
  balloons = [];
  popped = 0;
  missed = 0;
  balloonCount = 0;
  statusElement.textContent = `Popped: 0 / ${totalBalloons}`;
  gameOverDiv.classList.remove("show");
  gameOverDiv.style.display = "none";
}

startBtn.addEventListener("click", async () => {
  // Hide instructions + button; show canvas in their place
  if (instructionsDiv) instructionsDiv.style.display = "none";
  startBtn.style.display = "none";
  if (instructionsDiv && instructionsDiv.parentNode) {
    instructionsDiv.parentNode.insertBefore(canvas, instructionsDiv);
  }
  canvas.style.display = "block";

  if (!gameStarted) {
    resetGame();
    gameStarted = true;
    await initCamera();
    startSpawning();
    loop();
  }

  canvas.scrollIntoView({ block: "center", behavior: "smooth" });
});

if (playAgainBtn) {
  playAgainBtn.addEventListener("click", () => {
    // Hide overlay and restart immediately
    gameOverDiv.classList.remove("show");
    gameOverDiv.style.display = "none";

    if (instructionsDiv) instructionsDiv.style.display = "none";
    startBtn.style.display = "none";
    canvas.style.display = "block";
    if (instructionsDiv && instructionsDiv.parentNode) {
      instructionsDiv.parentNode.insertBefore(canvas, instructionsDiv);
    }
    resetGame();
    gameStarted = true;
    startSpawning();
    loop();
  });
}
