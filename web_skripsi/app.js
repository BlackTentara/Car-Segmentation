/* ============================================================
   SegWrap — Advanced Interactive Demo Logic with 3D & Animations
   ============================================================ */

'use strict';

// ─── State ───────────────────────────────────────────────────
let uploadedImage = null;   // HTMLImageElement
let maskData = null;        // ImageData (binary mask)
let currentStep = 1;
let selectedColor = '#dc2626';
let scene, camera, renderer, car3D;

// ─── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initUploadZone();
  initColorSwatches();
});

// ─── Particle Background (particles.js) ───────────────────────
function initParticles() {
  if (typeof particlesJS !== 'undefined') {
    particlesJS('particles-js', {
      particles: {
        number: { value: 80, density: { enable: true, value_area: 800 } },
        color: { value: '#00d4ff' },
        shape: { type: 'circle' },
        opacity: { value: 0.3, random: true, anim: { enable: true, speed: 0.5, opacity_min: 0.1 } },
        size: { value: 3, random: true },
        line_linked: { enable: true, distance: 150, color: '#00d4ff', opacity: 0.2, width: 1 },
        move: { enable: true, speed: 1.5, direction: 'none', random: true, out_mode: 'out' }
      },
      interactivity: {
        detect_on: 'canvas',
        events: { onhover: { enable: true, mode: 'grab' }, onclick: { enable: true, mode: 'push' } },
        modes: { grab: { distance: 140, line_linked: { opacity: 0.5 } }, push: { particles_nb: 4 } }
      },
      retina_detect: true
    });
  }
}

// ─── 3D Car Model (Three.js) ───────────────────────────────────
function init3DCar() {
  const container = document.getElementById('car3d-container');
  if (!container || typeof THREE === 'undefined') return;

  // Scene setup
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setClearColor(0x000000, 0);
  container.appendChild(renderer.domElement);

  // Lights
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambientLight);
  const pointLight1 = new THREE.PointLight(0x00d4ff, 1.5, 100);
  pointLight1.position.set(10, 10, 10);
  scene.add(pointLight1);
  const pointLight2 = new THREE.PointLight(0x8b5cf6, 1, 100);
  pointLight2.position.set(-10, -10, 5);
  scene.add(pointLight2);

  // Create simplified 3D car
  const carGroup = new THREE.Group();

  // Body
  const bodyGeo = new THREE.BoxGeometry(4, 1.5, 2);
  const bodyMat = new THREE.MeshPhongMaterial({
    color: 0x1e293b,
    shininess: 80,
    emissive: 0x0a0f1a,
    specular: 0x00d4ff
  });
  const body = new THREE.Mesh(bodyGeo, bodyMat);
  body.position.y = 0.75;
  carGroup.add(body);

  // Cabin
  const cabinGeo = new THREE.BoxGeometry(2.5, 1.2, 1.8);
  const cabinMat = new THREE.MeshPhongMaterial({
    color: 0x1a2540,
    shininess: 100,
    emissive: 0x0a0f1a,
    specular: 0x00d4ff
  });
  const cabin = new THREE.Mesh(cabinGeo, cabinMat);
  cabin.position.set(-0.2, 1.8, 0);
  carGroup.add(cabin);

  // Windows (with transparency)
  const windowMat = new THREE.MeshPhongMaterial({
    color: 0x00d4ff,
    transparent: true,
    opacity: 0.3,
    shininess: 100,
    emissive: 0x001a24
  });

  const windowGeo = new THREE.BoxGeometry(0.9, 0.8, 1.7);
  const windowFront = new THREE.Mesh(windowGeo, windowMat);
  windowFront.position.set(0.5, 1.8, 0);
  carGroup.add(windowFront);

  const windowBack = new THREE.Mesh(windowGeo, windowMat);
  windowBack.position.set(-0.9, 1.8, 0);
  carGroup.add(windowBack);

  // Wheels
  const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16);
  const wheelMat = new THREE.MeshPhongMaterial({
    color: 0x1a1a1a,
    shininess: 50,
    emissive: 0x050505
  });

  const rimGeo = new THREE.CylinderGeometry(0.25, 0.25, 0.32, 16);
  const rimMat = new THREE.MeshPhongMaterial({
    color: 0x00d4ff,
    emissive: 0x003344,
    shininess: 100
  });

  const positions = [
    { x: 1.3, z: 1.1 },
    { x: 1.3, z: -1.1 },
    { x: -1.3, z: 1.1 },
    { x: -1.3, z: -1.1 }
  ];

  positions.forEach(pos => {
    const wheel = new THREE.Mesh(wheelGeo, wheelMat);
    wheel.position.set(pos.x, 0.4, pos.z);
    wheel.rotation.z = Math.PI / 2;
    carGroup.add(wheel);

    const rim = new THREE.Mesh(rimGeo, rimMat);
    rim.position.set(pos.x, 0.4, pos.z);
    rim.rotation.z = Math.PI / 2;
    carGroup.add(rim);
  });

  // Add glow effect
  const glowGeo = new THREE.BoxGeometry(4.3, 1.7, 2.3);
  const glowMat = new THREE.MeshBasicMaterial({
    color: 0x00d4ff,
    transparent: true,
    opacity: 0.1,
    side: THREE.BackSide
  });
  const glow = new THREE.Mesh(glowGeo, glowMat);
  glow.position.y = 0.75;
  carGroup.add(glow);

  scene.add(carGroup);
  car3D = carGroup;

  camera.position.set(5, 3, 5);
  camera.lookAt(0, 1, 0);

  // Animation loop
  function animate() {
    requestAnimationFrame(animate);
    if (car3D) {
      car3D.rotation.y += 0.005;
      car3D.position.y = Math.sin(Date.now() * 0.001) * 0.1;
    }
    renderer.render(scene, camera);
  }
  animate();

  // Handle resize
  window.addEventListener('resize', () => {
    if (container.clientWidth > 0) {
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    }
  });
}

// ─── GSAP Scroll Animations ───────────────────────────────────
function initGSAPAnimations() {
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);

  // Hero elements fade in with stagger
  gsap.from('.hero-badge', { opacity: 0, y: 30, duration: 0.8, delay: 0.2 });
  gsap.from('.hero-title', { opacity: 0, y: 40, duration: 0.8, delay: 0.4 });
  gsap.from('.hero-sub', { opacity: 0, y: 30, duration: 0.8, delay: 0.6 });
  gsap.from('.hero-actions', { opacity: 0, y: 30, duration: 0.8, delay: 0.8 });
  gsap.from('.hero-stats', { opacity: 0, y: 30, duration: 0.8, delay: 1 });
  gsap.from('.hero-visual', { opacity: 0, scale: 0.9, duration: 1, delay: 0.5 });

  // About cards (animations removed for better visibility)
  // gsap.from('.about-card', {
  //   scrollTrigger: { trigger: '#about', start: 'top 80%' },
  //   opacity: 0,
  //   y: 50,
  //   stagger: 0.2,
  //   duration: 0.8
  // });

  // Pipeline steps (animations removed for better visibility)
  // gsap.from('.pipe-step', {
  //   scrollTrigger: { trigger: '.pipeline', start: 'top 80%' },
  //   opacity: 0,
  //   scale: 0.8,
  //   stagger: 0.15,
  //   duration: 0.6
  // });

  // Neural network diagram
  gsap.from('.nn-layer', {
    scrollTrigger: { trigger: '.architecture-viz', start: 'top 75%' },
    opacity: 0,
    x: -30,
    stagger: 0.15,
    duration: 0.7
  });

  // Model cards animation removed - cards always visible

  // Chart cards animation removed - charts always visible

  // Parallax effect on blobs
  gsap.to('.blob1', {
    scrollTrigger: { trigger: '#hero', scrub: 1 },
    y: 100,
    x: 50,
    ease: 'none'
  });
  gsap.to('.blob2', {
    scrollTrigger: { trigger: '#hero', scrub: 1 },
    y: -80,
    x: -40,
    ease: 'none'
  });

  // Navbar background on scroll
  ScrollTrigger.create({
    start: 'top -80',
    end: 99999,
    toggleClass: { className: 'scrolled', targets: '#navbar' }
  });
}

// ─── Chart Bar Animations ─────────────────────────────────────
function initChartAnimations() {
  // Bar animations removed - bars now show immediately
  const bars = document.querySelectorAll('.animated-bar');
  bars.forEach(bar => {
    const targetHeight = parseFloat(bar.getAttribute('data-target-height'));
    const targetY = parseFloat(bar.getAttribute('data-target-y'));
    bar.setAttribute('height', targetHeight);
    bar.setAttribute('y', targetY);
  });
}

// ─── Navbar scroll effect ─────────────────────────────────────
function initNavScroll() {
  const nav = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    nav.style.background = window.scrollY > 60
      ? 'rgba(8,11,20,0.95)'
      : 'rgba(8,11,20,0.7)';
  });
}

// ─── Intersection Observer for section animations ─────────────
function observeSections() {
  // All animations removed for better visibility
  // Cards now stay visible without fade-in effects
}

// ─── Model card hover glow ────────────────────────────────────
function initModelCardHover() {
  const glowColors = {
    yolov8:  'rgba(0,212,255,0.15)',
    maskrcnn:'rgba(139,92,246,0.15)',
    solov2:  'rgba(16,185,129,0.15)',
    yolosam: 'rgba(249,115,22,0.15)',
    rtmdet:  'rgba(244,63,94,0.15)',
  };
  document.querySelectorAll('.model-card').forEach(card => {
    card.addEventListener('mouseenter', () => {
      card.style.boxShadow = `0 20px 50px ${glowColors[card.dataset.model] || 'rgba(0,212,255,0.1)'}`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.boxShadow = '';
    });
  });
}

// ─── Step navigation ─────────────────────────────────────────
function goToStep(n) {
  currentStep = n;
  [1, 2, 3].forEach(i => {
    document.getElementById(`panel-${i}`).style.display = i === n ? 'block' : 'none';
    const navItem = document.getElementById(`step-nav-${i}`);
    navItem.classList.remove('active', 'done');
    if (i === n) navItem.classList.add('active');
    else if (i < n) navItem.classList.add('done');
  });

  // When going to step 3, show original image immediately
  if (n === 3 && uploadedImage) {
    document.getElementById('colorOrigImg').src = uploadedImage.src;
  }

  // Smooth scroll to demo section
  document.getElementById('demo').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ─── Upload Zone ──────────────────────────────────────────────
function initUploadZone() {
  const zone = document.getElementById('uploadZone');
  const input = document.getElementById('fileInput');

  zone.addEventListener('click', () => input.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) loadFile(file);
  });
  input.addEventListener('change', () => {
    if (input.files[0]) loadFile(input.files[0]);
  });
}

function loadFile(file) {
  if (!file.type.match(/image\/(jpeg|png)/)) {
    alert('Please upload a JPG or PNG image.');
    return;
  }
  const reader = new FileReader();
  reader.onload = e => {
    const img = new Image();
    img.onload = () => {
      uploadedImage = img;
      document.getElementById('previewImg').src = e.target.result;
      document.getElementById('fileName').textContent = file.name;
      document.getElementById('uploadZone').style.display = 'none';
      document.getElementById('previewArea').style.display = 'block';
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

function resetUpload() {
  uploadedImage = null;
  maskData = null;
  document.getElementById('fileInput').value = '';
  document.getElementById('uploadZone').style.display = 'block';
  document.getElementById('previewArea').style.display = 'none';
}

// ─── Mask Generation (REAL API CALL) ─────────────────────────
async function generateMask() {
  if (!uploadedImage) { alert('Please upload an image first.'); return; }

  const modelValue = document.getElementById('modelSelect').value;
  const methodValue = document.getElementById('methodSelect').value;
  const useCarDetector = document.getElementById('useCarDetector').checked;

  const modelName = {
    yolact:  'YOLACT',
    maskrcnn:'Mask R-CNN',
    htc:     'HTC',
    yolosam: 'YOLO-SAM',
  }[modelValue] || modelValue.toUpperCase();

  const methodName = methodValue === 'method1' ? 'Direct Wrappable' : 'Car Minus Unwrappable';

  document.getElementById('loadingModel').textContent = `${modelName} (${methodName})`;
  document.getElementById('maskLoading').style.display = 'flex';
  document.getElementById('comparisonView').style.display = 'none';
  document.getElementById('toStep3Btn').style.display = 'none';

  try {
    // Convert image to base64
    const canvas = document.createElement('canvas');
    canvas.width = uploadedImage.naturalWidth || uploadedImage.width;
    canvas.height = uploadedImage.naturalHeight || uploadedImage.height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(uploadedImage, 0, 0);
    const imageBase64 = canvas.toDataURL('image/png');

    // Call backend API
    const response = await fetch('http://localhost:5000/api/segment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image: imageBase64,
        model: modelValue,
        method: methodValue,
        confidence: 0.5,
        use_car_detector: useCarDetector
      })
    });

    if (!response.ok) {
      const errorData = await response.json();

      // Check if it's a "no vehicle detected" error
      if (errorData.error && errorData.error.toLowerCase().includes('no vehicle')) {
        throw new Error(errorData.message || errorData.error);
      }

      // Otherwise it's a different error
      throw new Error(errorData.error || 'Segmentation failed');
    }

    const result = await response.json();

    // Load mask as ImageData
    const maskImg = new Image();
    maskImg.onload = () => {
      const W = maskImg.width;
      const H = maskImg.height;
      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = W;
      tempCanvas.height = H;
      const tempCtx = tempCanvas.getContext('2d');
      tempCtx.drawImage(maskImg, 0, 0);
      maskData = tempCtx.getImageData(0, 0, W, H);

      // Display results
      renderMask(maskData);
      document.getElementById('maskLoading').style.display = 'none';
      document.getElementById('comparisonView').style.display = 'grid';
      document.getElementById('origImg').src = uploadedImage.src;
      document.getElementById('toStep3Btn').style.display = 'block';
    };
    maskImg.src = result.mask;

  } catch (error) {
    console.error('Segmentation error:', error);

    // Check if it's a network error (backend not running)
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      alert(`❌ Cannot connect to backend server\n\nMake sure the Flask backend is running:\n  python app.py`);
    }
    // Check if it's a "no vehicle" error
    else if (error.message.toLowerCase().includes('vehicle') || error.message.toLowerCase().includes('car')) {
      alert(`⚠️ ${error.message}`);
    }
    // Other errors
    else {
      alert(`❌ Error: ${error.message}`);
    }

    document.getElementById('maskLoading').style.display = 'none';
  }
}

function simulateMask(img) {
  const W = img.naturalWidth  || img.width;
  const H = img.naturalHeight || img.height;
  const off = new OffscreenCanvas(W, H);
  const ctx = off.getContext('2d');
  ctx.drawImage(img, 0, 0, W, H);
  const raw = ctx.getImageData(0, 0, W, H);
  const mask = new ImageData(W, H);

  // Simple luminance-based placeholder mask — treats mid-tone pixels as "vehicle"
  for (let i = 0; i < raw.data.length; i += 4) {
    const r = raw.data[i], g = raw.data[i+1], b = raw.data[i+2];
    const lum = 0.299*r + 0.587*g + 0.114*b;
    // Keep pixels that are not very dark (shadow) and not very bright (sky/background)
    const isCar = lum > 40 && lum < 230;
    mask.data[i]   = isCar ? 255 : 30;
    mask.data[i+1] = isCar ? 255 : 30;
    mask.data[i+2] = isCar ? 255 : 30;
    mask.data[i+3] = 255;
  }
  return mask;
}

function renderMask(imageData) {
  const canvas = document.getElementById('maskCanvas');
  canvas.width  = imageData.width;
  canvas.height = imageData.height;
  const ctx = canvas.getContext('2d');

  // Colorize mask: white → cyan, black → dark
  const colored = new ImageData(imageData.width, imageData.height);
  for (let i = 0; i < imageData.data.length; i += 4) {
    const on = imageData.data[i] > 128;
    colored.data[i]   = on ? 0   : 8;
    colored.data[i+1] = on ? 212 : 11;
    colored.data[i+2] = on ? 255 : 20;
    colored.data[i+3] = 255;
  }
  ctx.putImageData(colored, 0, 0);
}

// ─── Color Swatches ───────────────────────────────────────────
function initColorSwatches() {
  document.querySelectorAll('.preset-swatch').forEach(swatch => {
    swatch.addEventListener('click', () => {
      document.querySelectorAll('.preset-swatch').forEach(s => s.classList.remove('selected'));
      swatch.classList.add('selected');
      selectedColor = swatch.dataset.color;
      document.getElementById('customColor').value = selectedColor;
      updateRGBFromHex(selectedColor);
    });
  });
  document.getElementById('customColor').addEventListener('input', e => {
    selectedColor = e.target.value;
    document.querySelectorAll('.preset-swatch').forEach(s => s.classList.remove('selected'));
    updateRGBFromHex(selectedColor);
  });

  // RGB Sliders
  const rSlider = document.getElementById('rSlider');
  const gSlider = document.getElementById('gSlider');
  const bSlider = document.getElementById('bSlider');

  rSlider.addEventListener('input', updateColorFromRGB);
  gSlider.addEventListener('input', updateColorFromRGB);
  bSlider.addEventListener('input', updateColorFromRGB);

  // Select first swatch by default
  document.querySelector('.preset-swatch')?.classList.add('selected');
}

function updateRGBFromHex(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);

  document.getElementById('rSlider').value = r;
  document.getElementById('gSlider').value = g;
  document.getElementById('bSlider').value = b;
  document.getElementById('rValue').textContent = r;
  document.getElementById('gValue').textContent = g;
  document.getElementById('bValue').textContent = b;
}

function updateColorFromRGB() {
  const r = parseInt(document.getElementById('rSlider').value);
  const g = parseInt(document.getElementById('gSlider').value);
  const b = parseInt(document.getElementById('bSlider').value);

  document.getElementById('rValue').textContent = r;
  document.getElementById('gValue').textContent = g;
  document.getElementById('bValue').textContent = b;

  const hex = '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
  selectedColor = hex;
  document.getElementById('customColor').value = hex;
  document.querySelectorAll('.preset-swatch').forEach(s => s.classList.remove('selected'));
}

// ─── OLD Color Application (COMMENTED OUT - KEPT FOR REFERENCE) ──────
// async function applyColorOld() {
//   if (!uploadedImage || !maskData) { alert('Please generate a mask first.'); return; }
//
//   try {
//     // Convert image to base64
//     const canvas = document.createElement('canvas');
//     canvas.width = uploadedImage.naturalWidth || uploadedImage.width;
//     canvas.height = uploadedImage.naturalHeight || uploadedImage.height;
//     const ctx = canvas.getContext('2d');
//     ctx.drawImage(uploadedImage, 0, 0);
//     const imageBase64 = canvas.toDataURL('image/png');
//
//     // Convert mask to base64
//     const maskCanvas = document.createElement('canvas');
//     maskCanvas.width = maskData.width;
//     maskCanvas.height = maskData.height;
//     const maskCtx = maskCanvas.getContext('2d');
//     maskCtx.putImageData(maskData, 0, 0);
//     const maskBase64 = maskCanvas.toDataURL('image/png');
//
//     // Call backend API (OLD METHOD)
//     const response = await fetch('http://localhost:5000/api/colorize_old', {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({
//         image: imageBase64,
//         mask: maskBase64,
//         color: selectedColor
//       })
//     });
//
//     if (!response.ok) {
//       const error = await response.json();
//       throw new Error(error.error || 'Colorization failed');
//     }
//
//     const result = await response.json();
//
//     // Display result
//     const resultImg = new Image();
//     resultImg.onload = () => {
//       const resultCanvas = document.getElementById('resultCanvas');
//       resultCanvas.width = resultImg.width;
//       resultCanvas.height = resultImg.height;
//       const resultCtx = resultCanvas.getContext('2d');
//       resultCtx.drawImage(resultImg, 0, 0);
//
//       document.getElementById('colorOrigImg').src = uploadedImage.src;
//       document.getElementById('downloadBtn').style.display = 'inline-flex';
//     };
//     resultImg.src = result.result;
//
//   } catch (error) {
//     console.error('Colorization error:', error);
//     alert(`Error: ${error.message}\n\nMake sure the Flask backend is running (python app.py)`);
//   }
// }

// ─── Color Application (HYBRID LIGHTING-PRESERVING METHOD) ──────
async function applyColor() {
  if (!uploadedImage || !maskData) { alert('Please generate a mask first.'); return; }

  try {
    // Convert image to base64
    const canvas = document.createElement('canvas');
    canvas.width = uploadedImage.naturalWidth || uploadedImage.width;
    canvas.height = uploadedImage.naturalHeight || uploadedImage.height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(uploadedImage, 0, 0);
    const imageBase64 = canvas.toDataURL('image/png');

    // Convert mask to base64
    const maskCanvas = document.createElement('canvas');
    maskCanvas.width = maskData.width;
    maskCanvas.height = maskData.height;
    const maskCtx = maskCanvas.getContext('2d');
    maskCtx.putImageData(maskData, 0, 0);
    const maskBase64 = maskCanvas.toDataURL('image/png');

    // Call backend API (HYBRID method)
    const response = await fetch('http://localhost:5000/api/colorize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image: imageBase64,
        mask: maskBase64,
        color: selectedColor
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Colorization failed');
    }

    const result = await response.json();

    // Display result
    const resultImg = new Image();
    resultImg.onload = () => {
      const resultCanvas = document.getElementById('resultCanvas');
      resultCanvas.width = resultImg.width;
      resultCanvas.height = resultImg.height;
      const resultCtx = resultCanvas.getContext('2d');
      resultCtx.drawImage(resultImg, 0, 0);

      document.getElementById('colorOrigImg').src = uploadedImage.src;
      document.getElementById('downloadBtn').style.display = 'inline-flex';
    };
    resultImg.src = result.result;

  } catch (error) {
    console.error('Colorization error:', error);
    alert(`Error: ${error.message}\n\nMake sure the Flask backend is running (python app.py)`);
  }
}

function downloadResult() {
  const canvas = document.getElementById('resultCanvas');
  const a = document.createElement('a');
  a.href = canvas.toDataURL('image/png');
  a.download = 'carwrap_result.png';
  a.click();
}

// ─── Color Helpers ────────────────────────────────────────────
function hexToHsv(hex) {
  let r = parseInt(hex.slice(1,3),16)/255;
  let g = parseInt(hex.slice(3,5),16)/255;
  let b = parseInt(hex.slice(5,7),16)/255;
  return rgbToHsv(r*255, g*255, b*255);
}

function rgbToHsv(r, g, b) {
  r/=255; g/=255; b/=255;
  const max=Math.max(r,g,b), min=Math.min(r,g,b), d=max-min;
  let h=0, s=max===0?0:d/max, v=max;
  if(d!==0){
    if(max===r) h=((g-b)/d)%6;
    else if(max===g) h=(b-r)/d+2;
    else h=(r-g)/d+4;
    h/=6; if(h<0) h+=1;
  }
  return [h, s, v];
}

function hsvToRgb(h, s, v) {
  let r,g,b;
  const i=Math.floor(h*6), f=h*6-i;
  const p=v*(1-s), q=v*(1-f*s), t=v*(1-(1-f)*s);
  switch(i%6){
    case 0: r=v;g=t;b=p;break;
    case 1: r=q;g=v;b=p;break;
    case 2: r=p;g=v;b=t;break;
    case 3: r=p;g=q;b=v;break;
    case 4: r=t;g=p;b=v;break;
    case 5: r=v;g=p;b=q;break;
  }
  return [Math.round(r*255), Math.round(g*255), Math.round(b*255)];
}
