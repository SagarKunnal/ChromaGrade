// ChromaGrade Pro — Studio Client Engine (Light Mode)
// Streamlined Single-Page Architecture with Static Grading Monitor

document.addEventListener("DOMContentLoaded", () => {
  // State
  let sourceFile = null;
  let sourceUrl = "/static/demo/color_input1.jpg";
  let refFile = null;
  let refUrl = "/static/demo/color_reference_1.jpg";
  let latestResultData = null;
  let activeViewMode = "split";
  let isDraggingSplit = false;

  // DOM Elements - Studio Uploads & Controls
  const sourceDropzone = document.getElementById("sourceDropzone");
  const sourceFileInput = document.getElementById("sourceFileInput");
  const sourcePlaceholder = document.getElementById("sourcePlaceholder");
  const sourcePreviewBox = document.getElementById("sourcePreviewBox");
  const sourcePreviewImg = document.getElementById("sourcePreviewImg");
  const removeSourceBtn = document.getElementById("removeSourceBtn");

  const refDropzone = document.getElementById("refDropzone");
  const refFileInput = document.getElementById("refFileInput");
  const refPlaceholder = document.getElementById("refPlaceholder");
  const refPreviewBox = document.getElementById("refPreviewBox");
  const refPreviewImg = document.getElementById("refPreviewImg");
  const removeRefBtn = document.getElementById("removeRefBtn");

  const resetWorkspaceBtn = document.getElementById("resetWorkspaceBtn");

  const algorithmSelect = document.getElementById("algorithmSelect");
  const activeAlgoBadge = document.getElementById("activeAlgoBadge");
  const strengthSlider = document.getElementById("strengthSlider");
  const strengthValue = document.getElementById("strengthValue");
  const satSlider = document.getElementById("satSlider");
  const satValue = document.getElementById("satValue");
  const tempSlider = document.getElementById("tempSlider");
  const tempValue = document.getElementById("tempValue");
  const contrastSlider = document.getElementById("contrastSlider");
  const contrastValue = document.getElementById("contrastValue");
  const brightnessSlider = document.getElementById("brightnessSlider");
  const brightnessValue = document.getElementById("brightnessValue");
  const vignetteSlider = document.getElementById("vignetteSlider");
  const vignetteValue = document.getElementById("vignetteValue");
  const preserveLumCheckbox = document.getElementById("preserveLumCheckbox");

  const applyGradeBtn = document.getElementById("applyGradeBtn");
  const btnText = document.getElementById("btnText");
  const loadingOverlay = document.getElementById("loadingOverlay");
  const emptyState = document.getElementById("emptyState");
  const timingBadge = document.getElementById("timingBadge");

  // DOM Elements - Viewports
  const splitViewContainer = document.getElementById("splitViewContainer");
  const sourceImgSplit = document.getElementById("sourceImgSplit");
  const gradedImgSplit = document.getElementById("gradedImgSplit");
  const compareOverlay = document.getElementById("compareOverlay");
  const compareHandle = document.getElementById("compareHandle");

  const sideBySideContainer = document.getElementById("sideBySideContainer");
  const sourceImgSide = document.getElementById("sourceImgSide");
  const gradedImgSide = document.getElementById("gradedImgSide");

  const gradedOnlyContainer = document.getElementById("gradedOnlyContainer");
  const gradedImgOnly = document.getElementById("gradedImgOnly");

  // DOM Elements - Palettes & Scopes
  const paletteCard = document.getElementById("paletteCard");
  const paletteSwatches = document.getElementById("paletteSwatches");
  const dotShadows = document.getElementById("dotShadows");
  const dotMidtones = document.getElementById("dotMidtones");
  const dotHighlights = document.getElementById("dotHighlights");
  const valShadows = document.getElementById("valShadows");
  const valMidtones = document.getElementById("valMidtones");
  const valHighlights = document.getElementById("valHighlights");

  const downloadImgBtn = document.getElementById("downloadImgBtn");
  const downloadLutBtn = document.getElementById("downloadLutBtn");
  const copyImgBtn = document.getElementById("copyImgBtn");
  const historySection = document.getElementById("historySection");
  const historyThumbnails = document.getElementById("historyThumbnails");

  // =========================================================================
  // 1. BACKGROUND PARALLAX (Subtle Ambient Movement Only)
  // Note: The grading monitor is kept completely STATIC as requested!
  // =========================================================================
  const parallaxGrid = document.getElementById("parallaxGrid");
  const parallaxOrbAmber = document.getElementById("parallaxOrbAmber");
  const parallaxOrbCyan = document.getElementById("parallaxOrbCyan");

  window.addEventListener("mousemove", (e) => {
    const mouseX = e.clientX / window.innerWidth - 0.5;
    const mouseY = e.clientY / window.innerHeight - 0.5;

    if (parallaxGrid) {
      parallaxGrid.style.transform = `translate(${mouseX * -16}px, ${mouseY * -16}px)`;
    }
    if (parallaxOrbAmber) {
      parallaxOrbAmber.style.transform = `translate(${mouseX * 30}px, ${mouseY * 30}px)`;
    }
    if (parallaxOrbCyan) {
      parallaxOrbCyan.style.transform = `translate(${mouseX * -35}px, ${mouseY * -35}px)`;
    }
  });

  // =========================================================================
  // 2. TOAST NOTIFICATIONS
  // =========================================================================
  function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    const toastMsg = document.getElementById("toastMsg");
    const toastIcon = document.getElementById("toastIcon");

    toastMsg.textContent = message;
    if (isError) {
      toastIcon.setAttribute("data-lucide", "alert-circle");
      toastIcon.className = "w-4 h-4 text-rose-400";
    } else {
      toastIcon.setAttribute("data-lucide", "check-circle");
      toastIcon.className = "w-4 h-4 text-emerald-400";
    }
    lucide.createIcons();

    toast.classList.remove("translate-y-24", "opacity-0");
    toast.classList.add("translate-y-0", "opacity-100");

    setTimeout(() => {
      toast.classList.remove("translate-y-0", "opacity-100");
      toast.classList.add("translate-y-24", "opacity-0");
    }, 3200);
  }

  // =========================================================================
  // 3. IMAGE PREVIEW & DROPZONE LOGIC
  // =========================================================================
  function setSourcePreview(src, isFileObj = false) {
    if (isFileObj) {
      sourceFile = src;
      sourceUrl = null;
      const objectUrl = URL.createObjectURL(src);
      sourcePreviewImg.src = objectUrl;
    } else {
      sourceFile = null;
      sourceUrl = src;
      sourcePreviewImg.src = src;
    }
    sourcePlaceholder.classList.add("hidden");
    sourcePreviewBox.classList.remove("hidden");
  }

  function clearSourcePreview() {
    sourceFile = null;
    sourceUrl = null;
    sourceFileInput.value = "";
    sourcePreviewImg.src = "";
    sourcePreviewBox.classList.add("hidden");
    sourcePlaceholder.classList.remove("hidden");
  }

  function setRefPreview(src, isFileObj = false) {
    if (isFileObj) {
      refFile = src;
      refUrl = null;
      const objectUrl = URL.createObjectURL(src);
      refPreviewImg.src = objectUrl;
    } else {
      refFile = null;
      refUrl = src;
      refPreviewImg.src = src;
    }
    refPlaceholder.classList.add("hidden");
    refPreviewBox.classList.remove("hidden");
  }

  function clearRefPreview() {
    refFile = null;
    refUrl = null;
    refFileInput.value = "";
    refPreviewImg.src = "";
    refPreviewBox.classList.add("hidden");
    refPlaceholder.classList.remove("hidden");
  }

  // Source Drag-and-Drop & File Picker
  sourceDropzone.addEventListener("click", (e) => {
    if (e.target.closest("#removeSourceBtn")) return;
    sourceFileInput.click();
  });

  sourceFileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      setSourcePreview(e.target.files[0], true);
      showToast("Source photo loaded!");
    }
  });

  removeSourceBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearSourcePreview();
  });

  sourceDropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    sourceDropzone.classList.add("border-amber-500", "bg-amber-50/50");
  });

  sourceDropzone.addEventListener("dragleave", () => {
    sourceDropzone.classList.remove("border-amber-500", "bg-amber-50/50");
  });

  sourceDropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    sourceDropzone.classList.remove("border-amber-500", "bg-amber-50/50");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSourcePreview(e.dataTransfer.files[0], true);
      showToast("Source photo loaded!");
    }
  });

  // Reference Drag-and-Drop & File Picker
  refDropzone.addEventListener("click", (e) => {
    if (e.target.closest("#removeRefBtn")) return;
    refFileInput.click();
  });

  refFileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      setRefPreview(e.target.files[0], true);
      showToast("Reference style photo loaded!");
    }
  });

  removeRefBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearRefPreview();
  });

  refDropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    refDropzone.classList.add("border-cyan-500", "bg-cyan-50/50");
  });

  refDropzone.addEventListener("dragleave", () => {
    refDropzone.classList.remove("border-cyan-500", "bg-cyan-50/50");
  });

  refDropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    refDropzone.classList.remove("border-cyan-500", "bg-cyan-50/50");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setRefPreview(e.dataTransfer.files[0], true);
      showToast("Reference style photo loaded!");
    }
  });

  // Sample Buttons Hookup
  document.querySelectorAll(".sample-input-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      setSourcePreview(btn.dataset.url, false);
      showToast("Loaded sample input photo");
    });
  });

  document.querySelectorAll(".sample-ref-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      setRefPreview(btn.dataset.url, false);
      showToast("Loaded sample reference mood");
    });
  });

  // =========================================================================
  // 4. DARKROOM SLIDERS & CONTROLS
  // =========================================================================
  function updateAlgoBadge() {
    const names = {
      reinhard: "Reinhard LAB",
      cdf: "Cinematic CDF",
      split_tone: "Split-Tone Film",
      bilateral: "Bilateral Edge",
    };
    if (activeAlgoBadge) {
      activeAlgoBadge.textContent = names[algorithmSelect.value] || "Custom";
    }
  }

  algorithmSelect.addEventListener("change", updateAlgoBadge);

  strengthSlider.addEventListener("input", () => {
    strengthValue.textContent = `${strengthSlider.value}%`;
  });

  satSlider.addEventListener("input", () => {
    const val = parseInt(satSlider.value);
    satValue.textContent = val > 0 ? `+${val}%` : `${val}%`;
  });

  tempSlider.addEventListener("input", () => {
    const val = parseInt(tempSlider.value);
    tempValue.textContent = val > 0 ? `+${val}` : `${val}`;
  });

  contrastSlider.addEventListener("input", () => {
    const val = parseInt(contrastSlider.value);
    contrastValue.textContent = val > 0 ? `+${val}` : `${val}`;
  });

  brightnessSlider.addEventListener("input", () => {
    const val = parseInt(brightnessSlider.value);
    brightnessValue.textContent = val > 0 ? `+${val}` : `${val}`;
  });

  vignetteSlider.addEventListener("input", () => {
    vignetteValue.textContent = `${vignetteSlider.value}%`;
  });

  // Reset to defaults
  resetWorkspaceBtn.addEventListener("click", () => {
    strengthSlider.value = 100;
    strengthValue.textContent = "100%";
    satSlider.value = 0;
    satValue.textContent = "0%";
    tempSlider.value = 0;
    tempValue.textContent = "0";
    contrastSlider.value = 0;
    contrastValue.textContent = "0";
    brightnessSlider.value = 0;
    brightnessValue.textContent = "0";
    vignetteSlider.value = 0;
    vignetteValue.textContent = "0%";
    preserveLumCheckbox.checked = false;
    algorithmSelect.value = "reinhard";
    updateAlgoBadge();
    showToast("Grading controls reset to defaults.");
  });

  // =========================================================================
  // 5. COLOR TRANSFER MASTER API CALL
  // =========================================================================
  async function applyColorGrade() {
    if (!sourceFile && !sourceUrl) {
      showToast("Please provide an Input Image (Source)", true);
      return;
    }
    if (!refFile && !refUrl) {
      showToast("Please provide a Reference Image", true);
      return;
    }

    loadingOverlay.classList.remove("hidden");
    applyGradeBtn.disabled = true;
    btnText.textContent = "TRANSFERRING MOOD...";

    const formData = new FormData();

    // Source
    if (sourceFile) {
      formData.append("source_file", sourceFile);
    } else {
      formData.append("source_url", sourceUrl);
    }

    // Reference
    if (refFile) {
      formData.append("reference_file", refFile);
    } else {
      formData.append("reference_url", refUrl);
    }

    // Parameters
    formData.append("algorithm", algorithmSelect.value);
    formData.append("strength", (parseFloat(strengthSlider.value) / 100.0).toFixed(2));
    formData.append("preserve_luminance", preserveLumCheckbox.checked ? "true" : "false");
    formData.append("saturation", (parseFloat(satSlider.value) / 100.0).toFixed(2));
    formData.append("temperature", (parseFloat(tempSlider.value) / 100.0).toFixed(2));
    formData.append("contrast", (parseFloat(contrastSlider.value) / 100.0).toFixed(2));
    formData.append("brightness", (parseFloat(brightnessSlider.value) / 100.0).toFixed(2));
    formData.append("vignette", (parseFloat(vignetteSlider.value) / 100.0).toFixed(2));

    try {
      const response = await fetch("/api/transfer", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Color transfer failed");
      }

      const data = await response.json();
      latestResultData = data;
      renderResults(data);
      showToast(`Color grade applied in ${data.processing_time_ms}ms!`);
    } catch (err) {
      console.error(err);
      showToast(`Error: ${err.message}`, true);
    } finally {
      loadingOverlay.classList.add("hidden");
      applyGradeBtn.disabled = false;
      btnText.textContent = "APPLY COLOR GRADE";
    }
  }

  applyGradeBtn.addEventListener("click", applyColorGrade);

  // =========================================================================
  // 6. RESULTS RENDERING & BEFORE/AFTER SPLIT SLIDER
  // =========================================================================
  function renderResults(data) {
    emptyState.classList.add("hidden");

    // Timing Badge
    timingBadge.textContent = `${data.processing_time_ms}ms (${data.algorithm.toUpperCase()})`;
    timingBadge.classList.remove("hidden");

    // Source image representation
    const currentSourceSrc = sourceFile ? URL.createObjectURL(sourceFile) : sourceUrl;
    const gradedSrc = data.image_data;

    // 1. Split View
    sourceImgSplit.src = currentSourceSrc;
    gradedImgSplit.src = gradedSrc;

    // 2. Side-by-Side View
    sourceImgSide.src = currentSourceSrc;
    gradedImgSide.src = gradedSrc;

    // 3. Graded Only
    gradedImgOnly.src = gradedSrc;

    // Switch view mode
    setViewMode(activeViewMode);

    // Render Dominant Color Palette
    renderPalette(data.palette || []);

    // Update 3-Way Color Balance Wheels based on palette
    updateColorWheels(data.palette || []);

    // Enable Export Toolbar Buttons
    downloadImgBtn.disabled = false;
    downloadLutBtn.disabled = false;
    copyImgBtn.disabled = false;

    // Add to history strip
    addHistoryItem(gradedSrc, data.algorithm);
  }

  function setViewMode(mode) {
    activeViewMode = mode;
    document.querySelectorAll(".view-mode-btn").forEach((btn) => {
      if (btn.dataset.mode === mode) {
        btn.className = "view-mode-btn px-2.5 py-1 rounded-md text-[11px] font-semibold text-amber-700 bg-white shadow-xs transition";
      } else {
        btn.className = "view-mode-btn px-2.5 py-1 rounded-md text-[11px] font-medium text-slate-600 hover:text-slate-900 transition";
      }
    });

    splitViewContainer.classList.add("hidden");
    sideBySideContainer.classList.add("hidden");
    gradedOnlyContainer.classList.add("hidden");

    if (mode === "split") {
      splitViewContainer.classList.remove("hidden");
      resetSplitSlider();
    } else if (mode === "side") {
      sideBySideContainer.classList.remove("hidden");
    } else if (mode === "result") {
      gradedOnlyContainer.classList.remove("hidden");
    }
  }

  document.querySelectorAll(".view-mode-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      setViewMode(btn.dataset.mode);
    });
  });

  // Split Slider Drag Physics
  function resetSplitSlider() {
    setSplitPosition(50);
  }

  function setSplitPosition(pct) {
    const clamped = Math.max(0, Math.min(100, pct));
    compareOverlay.style.width = `${clamped}%`;
    compareHandle.style.left = `${clamped}%`;
  }

  function onSplitDrag(e) {
    if (!isDraggingSplit) return;
    const rect = splitViewContainer.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const x = clientX - rect.left;
    const pct = (x / rect.width) * 100;
    setSplitPosition(pct);
  }

  splitViewContainer.addEventListener("mousedown", (e) => {
    isDraggingSplit = true;
    onSplitDrag(e);
  });

  splitViewContainer.addEventListener("touchstart", (e) => {
    isDraggingSplit = true;
    onSplitDrag(e);
  });

  window.addEventListener("mousemove", onSplitDrag);
  window.addEventListener("touchmove", onSplitDrag);

  window.addEventListener("mouseup", () => {
    isDraggingSplit = false;
  });
  window.addEventListener("touchend", () => {
    isDraggingSplit = false;
  });

  // Double click split slider to snap back to center
  splitViewContainer.addEventListener("dblclick", () => {
    setSplitPosition(50);
  });

  // =========================================================================
  // 7. PALETTE RENDERING & 3-WAY COLOR BALANCE SCOPES
  // =========================================================================
  function renderPalette(palette) {
    if (!palette || palette.length === 0) {
      paletteCard.classList.add("hidden");
      return;
    }
    paletteCard.classList.remove("hidden");
    paletteSwatches.innerHTML = "";

    palette.forEach((color) => {
      const chip = document.createElement("div");
      chip.className = "palette-chip interactive-spring";
      chip.innerHTML = `
        <div class="palette-swatch-box" style="background-color: ${color.hex};"></div>
        <div class="text-[10px] font-mono font-bold text-slate-800 tracking-wide">${color.hex.toUpperCase()}</div>
        <div class="text-[9px] text-slate-500 truncate">${color.name}</div>
        <div class="text-[8px] text-slate-400 font-mono">${color.percentage}%</div>
      `;

      chip.addEventListener("click", () => {
        navigator.clipboard.writeText(color.hex);
        showToast(`Copied ${color.hex} (${color.name}) to clipboard!`);
      });

      paletteSwatches.appendChild(chip);
    });
  }

  function updateColorWheels(palette) {
    if (!palette || palette.length < 3) return;

    const c0 = palette[0];
    const c1 = palette[1];
    const c2 = palette[2];

    // Shadows
    if (dotShadows && c0) {
      const offsetX = 50 + ((c0.rgb[0] - c0.rgb[2]) / 255) * 20;
      const offsetY = 50 + ((c0.rgb[1] - 128) / 255) * 20;
      dotShadows.style.left = `${offsetX.toFixed(1)}%`;
      dotShadows.style.top = `${offsetY.toFixed(1)}%`;
      dotShadows.style.backgroundColor = c0.hex;
      valShadows.textContent = c0.name;
    }

    // Midtones
    if (dotMidtones && c1) {
      const offsetX = 50 + ((c1.rgb[0] - c1.rgb[2]) / 255) * 20;
      const offsetY = 50 + ((c1.rgb[1] - 128) / 255) * 20;
      dotMidtones.style.left = `${offsetX.toFixed(1)}%`;
      dotMidtones.style.top = `${offsetY.toFixed(1)}%`;
      dotMidtones.style.backgroundColor = c1.hex;
      valMidtones.textContent = c1.name;
    }

    // Highlights
    if (dotHighlights && c2) {
      const offsetX = 50 + ((c2.rgb[0] - c2.rgb[2]) / 255) * 20;
      const offsetY = 50 + ((c2.rgb[1] - 128) / 255) * 20;
      dotHighlights.style.left = `${offsetX.toFixed(1)}%`;
      dotHighlights.style.top = `${offsetY.toFixed(1)}%`;
      dotHighlights.style.backgroundColor = c2.hex;
      valHighlights.textContent = c2.name;
    }
  }

  // Session History Strip
  function addHistoryItem(imageData, algo) {
    historySection.classList.remove("hidden");
    const thumb = document.createElement("div");
    thumb.className = "w-14 h-14 rounded-lg overflow-hidden border border-slate-200 shrink-0 cursor-pointer hover:border-amber-500 transition relative group shadow-xs";
    thumb.innerHTML = `
      <img src="${imageData}" class="w-full h-full object-cover" />
      <span class="absolute inset-0 bg-slate-900/60 opacity-0 group-hover:opacity-100 flex items-center justify-center text-[9px] font-mono text-white transition">${algo.toUpperCase()}</span>
    `;
    thumb.addEventListener("click", () => {
      latestResultData = { image_data: imageData, algorithm: algo, processing_time_ms: 0 };
      gradedImgSplit.src = imageData;
      gradedImgSide.src = imageData;
      gradedImgOnly.src = imageData;
      showToast("Restored from session history");
    });
    historyThumbnails.prepend(thumb);
  }

  // =========================================================================
  // 8. EXPORT ACTIONS (IMAGE, 3D LUT, CLIPBOARD)
  // =========================================================================
  downloadImgBtn.addEventListener("click", () => {
    if (!latestResultData || !latestResultData.image_data) return;
    const a = document.createElement("a");
    a.href = latestResultData.image_data;
    a.download = `chromagrade_${latestResultData.algorithm}_${Date.now()}.jpg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    showToast("Downloaded graded photograph!");
  });

  downloadLutBtn.addEventListener("click", async () => {
    if (!refFile && !refUrl) {
      showToast("Reference mood required to export 3D LUT", true);
      return;
    }
    await export3DLut(33);
  });

  copyImgBtn.addEventListener("click", async () => {
    if (!latestResultData || !latestResultData.image_data) return;
    try {
      const res = await fetch(latestResultData.image_data);
      const blob = await res.blob();
      await navigator.clipboard.write([
        new ClipboardItem({ [blob.type]: blob }),
      ]);
      showToast("Graded image copied to clipboard!");
    } catch (err) {
      console.error(err);
      showToast("Failed to copy image to clipboard", true);
    }
  });

  async function export3DLut(size = 33) {
    showToast(`Generating ${size}x${size}x${size} 3D .CUBE LUT...`);

    const formData = new FormData();
    if (refFile) {
      formData.append("reference_file", refFile);
    } else {
      formData.append("reference_url", refUrl);
    }
    formData.append("algorithm", algorithmSelect.value);
    formData.append("strength", (parseFloat(strengthSlider.value) / 100.0).toFixed(2));
    formData.append("preserve_luminance", preserveLumCheckbox.checked ? "true" : "false");
    formData.append("saturation", (parseFloat(satSlider.value) / 100.0).toFixed(2));
    formData.append("temperature", (parseFloat(tempSlider.value) / 100.0).toFixed(2));
    formData.append("contrast", (parseFloat(contrastSlider.value) / 100.0).toFixed(2));
    formData.append("brightness", (parseFloat(brightnessSlider.value) / 100.0).toFixed(2));
    formData.append("lut_size", size.toString());

    try {
      const res = await fetch("/api/export-lut", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to export 3D LUT");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `grade_${algorithmSelect.value}_${size}x${size}.cube`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      showToast(`Exported .CUBE 3D LUT (${size}x${size}x${size})!`);
    } catch (err) {
      console.error(err);
      showToast(`LUT export error: ${err.message}`, true);
    }
  }

  // =========================================================================
  // 9. INITIALIZATION
  // =========================================================================
  setSourcePreview(sourceUrl, false);
  setRefPreview(refUrl, false);
  updateAlgoBadge();
});
