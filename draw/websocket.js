const HOST = "localhost";
const PORT = 8765;

const ws = new WebSocket(`ws://${HOST}:${PORT}/ws`);

ws.onopen = () => {
  console.log("WebSocket connection established");
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("WebSocket connection closed");
};

let lastFrameTime = 0;

const sendCanvasFrame = () => {
  const MIN_INTERVAL = 1000 / 5;
  const IMAGE_QUALITY = 0.25;
  const SEND_CANVAS_SIZE = 256;

  const now = performance.now();
  if (now - lastFrameTime < MIN_INTERVAL) {
    console.log("Frame skipped due to rate limiting");
    return;
  }
  lastFrameTime = now;

  const canvas = document.getElementById("paint");

  // Create an offscreen canvas for resizing
  const offscreenCanvas = document.createElement("canvas");
  const offscreenCtx = offscreenCanvas.getContext("2d");

  offscreenCanvas.width = SEND_CANVAS_SIZE;
  offscreenCanvas.height = SEND_CANVAS_SIZE;

  // Draw the current canvas content onto the offscreen canvas
  offscreenCtx.drawImage(canvas, 0, 0, SEND_CANVAS_SIZE, SEND_CANVAS_SIZE);

  // Convert the offscreen canvas to a blob and send it
  offscreenCanvas.toBlob(
    (blob) => {
      if (blob && ws.readyState === WebSocket.OPEN) {
        const reader = new FileReader();
        reader.onload = () => {
          ws.send(reader.result);
        };
        reader.readAsArrayBuffer(blob);
      }
    },
    "image/webp",
    IMAGE_QUALITY
  );
};
