document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("paint");
  const ctx = canvas.getContext("2d");

  const toolStatus = {
    drawing: false,
    brushColor: "#ff0000",
    brushSize: 20,
    rainbow: false,
    eraser: false,
    hue: 0,
    mouse: { current: { x: 0, y: 0 }, last: { x: 0, y: 0 } },
    webcamStream: null,
    hexagonAnimation: false,
  };

  // Set canvas dimensions
  canvas.width = 512;
  canvas.height = 512;

  // Default brush settings
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.strokeStyle = toolStatus.brushColor;
  ctx.lineWidth = toolStatus.brushSize;

  const colorPicker = document.getElementById("colorPicker");
  const rainbowButton = document.getElementById("rainbowButton");
  const sizePicker = document.getElementById("sizePicker");
  const sizeDisplay = document.getElementById("sizeDisplay");
  const clearButton = document.getElementById("clearButton");
  const eraserButton = document.getElementById("eraserButton");
  const modeSelector = document.getElementById("modeSelector");
  const hexagonButton = document.getElementById("hexagonButton");

  const tools = [
    colorPicker,
    rainbowButton,
    sizePicker,
    clearButton,
    eraserButton,
  ];
  colorPicker.classList.add("selected");

  modeSelector.addEventListener("change", async (event) => {
    const mode = event.target.value;

    if (mode === "webcam") {
      // Start webcam feed
      if (!toolStatus.webcamStream) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
          });
          toolStatus.webcamStream = stream;
          const video = document.createElement("video");
          video.srcObject = stream;
          video.play();

          // Draw webcam feed on the canvas
          const drawWebcam = () => {
            if (modeSelector.value === "webcam") {
              ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
              sendCanvasFrame();
              requestAnimationFrame(drawWebcam);
            }
          };
          drawWebcam();
        } catch (error) {
          console.error("Error accessing webcam:", error);
        }
      }
    } else if (mode === "drawing") {
      // Stop webcam feed
      if (toolStatus.webcamStream) {
        toolStatus.webcamStream.getTracks().forEach((track) => track.stop());
        toolStatus.webcamStream = null;
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear canvas
    }
  });

  // Update mouse position
  canvas.addEventListener("mousemove", (e) => {
    toolStatus.mouse.last.x = toolStatus.mouse.current.x;
    toolStatus.mouse.last.y = toolStatus.mouse.current.y;

    toolStatus.mouse.current.x = e.offsetX;
    toolStatus.mouse.current.y = e.offsetY;
  });

  // Start drawing
  canvas.addEventListener("mousedown", () => {
    toolStatus.drawing = true;
    toolStatus.mouse.last.x = toolStatus.mouse.current.x;
    toolStatus.mouse.last.y = toolStatus.mouse.current.y;
    ctx.beginPath();
    ctx.moveTo(toolStatus.mouse.current.x, toolStatus.mouse.current.y);

    canvas.addEventListener("mousemove", onPaint);
  });

  // Stop drawing
  canvas.addEventListener("mouseup", () => {
    toolStatus.drawing = false;
    canvas.removeEventListener("mousemove", onPaint);
  });

  const manageActiveTool = (tool) => {
    tools.forEach((t) => {
      if (t !== tool) {
        t.classList.remove("selected"); // Remove highlight from other tools
      }
    });

    if (tool.id === "colorPicker") {
      colorPicker.classList.add("selected");
      toolStatus.rainbow = false;
      toolStatus.eraser = false;
      ctx.strokeStyle = colorPicker.value;
    }

    if (tool.id === "rainbowButton") {
      toolStatus.rainbow = !toolStatus.rainbow;
      if (toolStatus.rainbow) {
        toolStatus.eraser = false;
        colorPicker.classList.remove("selected");
        rainbowButton.classList.add("selected");
        eraserButton.classList.remove("selected");

        return;
      }

      ctx.strokeStyle = colorPicker.value; // Reset to selected color
      rainbowButton.classList.remove("selected");
      colorPicker.classList.add("selected");
    }

    if (tool.id === "eraserButton") {
      toolStatus.eraser = !toolStatus.eraser; // Toggle eraser mode
      if (toolStatus.eraser) {
        toolStatus.rainbow = false;
        colorPicker.classList.remove("selected");
        rainbowButton.classList.remove("selected");
        eraserButton.classList.add("selected");
        ctx.strokeStyle = "#000"; // Set stroke color to white for eraser
        return;
      }

      ctx.strokeStyle = colorPicker.value; // Reset to selected color
      eraserButton.classList.remove("selected");
      colorPicker.classList.add("selected");
    }

    if (tool.id === "clearButton") {
      ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas
      toolStatus.rainbow = false;
      toolStatus.eraser = false;
      clearButton.classList.add("selected");
      colorPicker.classList.remove("selected");
      rainbowButton.classList.remove("selected");
      eraserButton.classList.remove("selected");
      ctx.strokeStyle = colorPicker.value; // Reset to selected color
      setTimeout(() => {
        clearButton.classList.remove("selected"); // Remove highlight after a short delay
        colorPicker.classList.add("selected");
      }, 100);
    }

    if (tool.id === "hexagonButton") {
      if (toolStatus.hexagonAnimation) {
        console.log("Hexagon", toolStatus.hexagonAnimation);
        toolStatus.hexagonAnimation.stop();
        ctx.strokeStyle = colorPicker.value; // Reset to selected color
        eraserButton.classList.remove("selected");
        hexagonButton.classList.remove("selected");
        rainbowButton.classList.remove("selected");
        colorPicker.classList.add("selected");
      } else {
        console.log("Hexagon start", toolStatus.hexagonAnimation);
        toolStatus.hexagonAnimation = createHexagonAnimation(canvas);
        toolStatus.hexagonAnimation.start();
        toolStatus.rainbow = false;
        toolStatus.eraser = false;
        colorPicker.classList.remove("selected");
        rainbowButton.classList.remove("selected");
        eraserButton.classList.remove("selected");
        hexagonButton.classList.add("selected");
      }
    }
  };

  // Update colorPicker value when a new color is selected
  colorPicker.addEventListener("input", (e) => {
    manageActiveTool(colorPicker);
    ctx.strokeStyle = e.target.value;
  });

  colorPicker.addEventListener("click", () => {
    manageActiveTool(colorPicker);
  });

  // Toggle rainbow effect
  rainbowButton.addEventListener("click", () => {
    manageActiveTool(rainbowButton);
  });

  eraserButton.addEventListener("click", () => {
    manageActiveTool(eraserButton);
  });

  clearButton.addEventListener("click", () => {
    manageActiveTool(clearButton);
  });

  sizePicker.addEventListener("input", (e) => {
    const newSize = e.target.value;
    ctx.lineWidth = newSize; // Update brush size
    sizeDisplay.textContent = newSize; // Update size display
  });

  hexagonButton.addEventListener("click", () => {
    manageActiveTool(hexagonButton);
  });

  const hslToHex = (h, s, l) => {
    s /= 100;
    l /= 100;

    const k = (n) => (n + h / 30) % 12;
    const a = s * Math.min(l, 1 - l);
    const f = (n) =>
      Math.round(
        255 * (l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1))))
      );

    return `#${f(0).toString(16).padStart(2, "0")}${f(8)
      .toString(16)
      .padStart(2, "0")}${f(4).toString(16).padStart(2, "0")}`;
  };

  // Draw on canvas
  const onPaint = () => {
    if (!toolStatus.drawing) return;

    if (toolStatus.rainbow) {
      ctx.strokeStyle = `hsl(${toolStatus.hue}, 100%, 50%)`; // Set stroke color to rainbow
      colorPicker.value = hslToHex(toolStatus.hue, 100, 50); // Update color picker value to match rainbow color
      toolStatus.hue = (toolStatus.hue + 1) % 360; // Increment hue and loop back to 0 after 360
    }

    ctx.beginPath();
    ctx.moveTo(toolStatus.mouse.last.x, toolStatus.mouse.last.y); // Start from the last mouse position
    ctx.lineTo(toolStatus.mouse.current.x, toolStatus.mouse.current.y);
    ctx.stroke();

    sendCanvasFrame();
  };
});
