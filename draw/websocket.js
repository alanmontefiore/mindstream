const HOST = "213.173.109.169";
const PORT = 36545;

const IMAGE_QUALITY = 0.85;
const SEND_CANVAS_SIZE = 256;

const ws = new WebSocket(`ws://${HOST}:${PORT}/ws`);

ws.onopen = () => {
  console.log("WebSocket connection established");
  const status_data = {
    prompt: "psychedelic patterns, cats, colorful",
    width: 512,
    height: 512,
    quality: 85,
    seed: 42,
    num_inference_steps: 50,
    guidance_scale: 5.2,
  };
  ws.send(JSON.stringify(status_data));
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("WebSocket connection closed");
};

let lastFrameTime = 0;
let sendNextFrame = true;

const waitForResponse = () =>
  new Promise((resolve) => {
    const handler = (event) => {
      ws.removeEventListener("message", handler);
      sendNextFrame = true;
      console.log("Received response:", event.data);
      resolve(event.data);
    };
    ws.addEventListener("message", handler);
  });

const sendCanvasFrame = () => {
  if (!sendNextFrame) return;

  sendNextFrame = false;

  const canvas = document.getElementById("paint");
  const resultCanvas = document.getElementById("resultCanvas");

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
        reader.onload = async () => {
          ws.send(reader.result);

          const response = await waitForResponse();
          // populate the canvas with the received image
          const img = new Image();
          img.src = URL.createObjectURL(new Blob([response]));

          img.onload = () => {
            const ctx = resultCanvas.getContext("2d");
            ctx.drawImage(img, 0, 0, resultCanvas.width, resultCanvas.height);
            URL.revokeObjectURL(img.src);
          };

          img.onerror = (error) => {
            console.error("Error loading image:", error);
          };
        };
        reader.readAsArrayBuffer(blob);
      }
    },
    "image/webp",
    IMAGE_QUALITY
  );
};
