const status_data = {
  prompt: "psychedelic patterns, cats, colorful",
  width: 512,
  height: 512,
  quality: 85,
  seed: 42,
  num_inference_steps: 50,
  guidance_scale: 5.2,
};

document.addEventListener("DOMContentLoaded", () => {
  const updateButton = document.getElementById("updateButton");

  updateButton.addEventListener("click", () => {
    const promptInput = document.getElementById("promptInput").value;
    const qualityInput = parseInt(
      document.getElementById("qualityInput").value
    );
    const seedInput = parseInt(document.getElementById("seedInput").value);
    const guidanceInput = parseFloat(
      document.getElementById("guidanceInput").value
    );

    status_data.prompt = promptInput;
    status_data.quality = qualityInput;
    status_data.seed = seedInput;
    status_data.guidance_scale = guidanceInput;

    console.log(status_data);
    ws.send(JSON.stringify(status_data));
  });
});
