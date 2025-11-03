const video = document.getElementById("video");
const canvas = document.getElementById("output");
const ctx = canvas.getContext("2d");
const statusElement = document.getElementById("status");
const startBtn = document.getElementById("start-btn");
const gameOverDiv = document.getElementById("game-over");
const resultText = document.getElementById("result-text");
const playAgainBtn = document.getElementById("play-again-btn");

let balloons = [];
let popped = 0;
let width, height;
let totalBalloons = 30;
let balloonCount = 0;
let gameStarted = false;

// 🧠 Adjust canvas dynamically (keep it square)
function resizeCanvas() {
  const size = Math.min(window.innerWidth * 0.8, window.innerHeight * 0.8);
  width = canvas.width = size;
  height = canvas.height = size;
}
resizeCanvas();
window.addEventListener("resize", resizeCanvas);

// 🎈 Balloon setup
const balloonImages = [
  "assets/balloon1.png",
  "assets/balloon2.png",
  "assets/balloon3.png",
  "assets/balloon4.png",
  "assets/balloon5.png",
];
const popSound = new Audio("assets/pop.mp3");

function spawnBalloon() {
  if (balloonCount >= totalBalloons) return;
  const img = new Image();
  img.src = balloonImages[Math.floor(Math.random() * balloonImages.length)];
  const balloon = {
    img,
    x: Math.random() * (width - 80),
    y: height + 100,
    speed: 1.2 + Math.random() * 0.8,
    popped: false,
  };
  balloons.push(balloon);
  balloonCount++;
}

function drawBalloons() {
  for (let i = 0; i < balloons.length; i++) {
    const b = balloons[i];
    if (!b.popped) {
      b.y -= b.speed;
      ctx.drawImage(b.img, b.x, b.y, 80, 100);
      if (b.y + 100 < 0) balloons.splice(i, 1);
    }
  }
}

function checkCollision(x, y) {
  for (let i = 0; i < balloons.length; i++) {
    const b = balloons[i];
    if (!b.popped && x > b.x && x < b.x + 80 && y > b.y && y < b.y + 100) {
      b.popped = true;
      popped++;
      statusElement.textContent = `Popped: ${popped} / ${totalBalloons}`;
      popSound.play();
      balloons.splice(i, 1);
      break;
    }
  }
}

const hands = new Hands({
  locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
});

hands.setOptions({
  maxNumHands: 1,
  modelComplexity: 1,
  minDetectionConfidence: 0.7,
  minTrackingConfidence: 0.7,
});

hands.onResults((results) => {
  ctx.save();
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.translate(width, 0);
  ctx.scale(-1, 1);
  ctx.drawImage(results.image, 0, 0, width, height);
  ctx.restore();

  drawBalloons();

  if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
    const landmarks = results.multiHandLandmarks[0];
    const indexTip = landmarks[8];

    const x = width - indexTip.x * width;
    const y = indexTip.y * height;

    ctx.beginPath();
    ctx.arc(x, y, 10, 0, 2 * Math.PI);
    ctx.fillStyle = "rgba(255, 0, 0, 0.5)";
    ctx.fill();

    checkCollision(x, y);
  }

  // Game end check
  if (balloonCount >= totalBalloons && balloons.length === 0) {
    endGame();
  }
});

// 🎮 Start Game
startBtn.addEventListener("click", () => {
  startBtn.style.display = "none";
  gameOverDiv.style.display = "none";
  canvas.style.display = "block";
  statusElement.textContent = `Popped: 0 / ${totalBalloons}`;

  balloons = [];
  popped = 0;
  balloonCount = 0;
  gameStarted = true;

  const balloonInterval = setInterval(() => {
    if (balloonCount < totalBalloons) {
      spawnBalloon();
    } else {
      clearInterval(balloonInterval);
    }
  }, 1500);

  initCamera();
});

// 🧩 Game Over
function endGame() {
  gameStarted = false;
  canvas.style.display = "none";
  gameOverDiv.style.display = "block";
  resultText.textContent = `🎯 Game Over! You popped ${popped} out of ${totalBalloons} balloons! 🎈`;
}

// 🔁 Play Again
playAgainBtn.addEventListener("click", () => {
  gameOverDiv.style.display = "none";
  startBtn.style.display = "inline-block";
});

// 🎥 Initialize camera
async function initCamera() {
  const stream = await navigator.mediaDevices.getUserMedia({ video: true });
  video.srcObject = stream;

  const camera = new Camera(video, {
    onFrame: async () => {
      if (gameStarted) {
        await hands.send({ image: video });
      }
    },
    width: 640,
    height: 480,
  });
  camera.start();
}
