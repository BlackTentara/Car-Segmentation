"""
SegWrap Backend - Flask API for Instance Segmentation Inference
Supports 4 models: Mask R-CNN, HTC, YOLACT, YOLO-SAM
Supports 2 filtering methods: Direct Wrappable, Car Minus Unwrappable
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import torch
import cv2
import numpy as np
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image
import json
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__, static_folder='.')
CORS(app)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Model paths (relative to training folder)
MODEL_PATHS = {
    'maskrcnn': '../testing/best2/best_maskrcnn.pth',
    'htc': '../testing/best2/best_htc.pth',
    'yolact': '../testing/best2/best_yolact.pth',
    'yolosam': {
        'yolo': '../testing/best2/best_yolov11.pt',
        'sam': 'weights/efficient_sam_vitt.pt'  # Will download if not exists
    }
}

# Config paths for MMDetection models
CONFIG_PATHS = {
    'maskrcnn': 'mmdetection/configs/testing/maskrcnn_test.py',
    'htc': 'mmdetection/configs/testing/htc_test.py',
    'yolact': 'mmdetection/configs/testing/yolact_test.py'
}

# Class names (21 car parts)
CLASS_NAMES = [
    'Hood', 'Front_door', 'Rear_door', 'Front_fender', 'Rear_fender',
    'Trunk', 'Roof', 'Bumper', 'Front_panel', 'Rear_panel',
    'Fender', 'Quarter_panel', 'Windshield', 'Front_glass', 'Rear_glass',
    'Hood', 'Trunk_lid', 'Door', 'Panel', 'Back_bumper', 'Front_bumper'
]

# Wrappable/Unwrappable class IDs (1-based indexing)
WRAPPABLE_CLASSES = [1, 2, 6, 7, 8, 13, 15, 16, 17, 18, 20]  # 11 classes
UNWRAPPABLE_CLASSES = [3, 4, 5, 9, 10, 11, 12, 14, 19, 21]  # 10 classes (Grille moved here)

# Device configuration
DEVICE = 'cpu'  # Force CPU for compatibility
print(f"Using device: {DEVICE}")

# ============================================================================
# MODEL LOADING
# ============================================================================

models = {}
car_detector = None  # COCO YOLO for car detection pre-filter

def setup_mmdet_env():
    """Setup MMDetection environment (like Colab notebooks)"""
    import sys

    # Add mmdetection to Python path
    mmdet_path = Path('mmdetection').resolve()
    if mmdet_path.exists() and str(mmdet_path) not in sys.path:
        sys.path.insert(0, str(mmdet_path))
        print(f"✓ Added MMDetection to path: {mmdet_path}")

    # Try alternative mmdetection locations
    if not mmdet_path.exists():
        # Check if in training folder structure
        alt_paths = [
            Path('../training/maskrcnn/mmdetection').resolve(),
            Path('../training/htc/mmdetection').resolve(),
            Path('../training/yolact/mmdetection').resolve(),
        ]

        for alt_path in alt_paths:
            if alt_path.exists():
                sys.path.insert(0, str(alt_path))
                print(f"✓ Using MMDetection from: {alt_path}")
                break

def load_mmdet_model(model_name):
    """Load MMDetection models (Mask R-CNN, HTC, YOLACT)"""
    try:
        # Setup environment first
        setup_mmdet_env()

        from mmdet.apis import init_detector
        import mmcv

        # Try to find config and checkpoint
        config_path = Path(CONFIG_PATHS[model_name])
        checkpoint_path = Path(MODEL_PATHS[model_name])

        # If paths are relative, try to resolve them
        if not config_path.is_absolute():
            config_path = Path(__file__).parent / config_path
        if not checkpoint_path.is_absolute():
            checkpoint_path = Path(__file__).parent / checkpoint_path

        # Try alternative locations
        if not config_path.exists():
            # Try mmdetection/configs
            alt_config = Path('mmdetection/configs') / Path(CONFIG_PATHS[model_name]).name
            if alt_config.exists():
                config_path = alt_config

        if not config_path.exists():
            print(f"⚠️  Config not found: {config_path}")
            print(f"    Please run setup_windows.bat or setup.sh first")
            return None

        if not checkpoint_path.exists():
            print(f"⚠️  Checkpoint not found: {checkpoint_path}")
            print(f"    Make sure you've trained the models first")
            return None

        print(f"Loading {model_name}...")
        print(f"  Config: {config_path}")
        print(f"  Checkpoint: {checkpoint_path}")

        model = init_detector(str(config_path), str(checkpoint_path), device=DEVICE)
        print(f"✓ {model_name} loaded successfully")
        return model

    except Exception as e:
        print(f"✗ Failed to load {model_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_yolosam_model():
    """Load YOLO-SAM hybrid model"""
    try:
        from ultralytics import YOLO

        yolo_path = Path(MODEL_PATHS['yolosam']['yolo']).resolve()

        if not yolo_path.exists():
            print(f"⚠️  YOLO model not found: {yolo_path}")
            return None

        print(f"Loading YOLO-SAM...")
        print(f"  YOLO: {yolo_path}")

        yolo_model = YOLO(str(yolo_path))

        # Load EfficientSAM
        try:
            from efficient_sam.build_efficient_sam import build_efficient_sam_vitt

            # Download SAM weights if not exists
            sam_path = Path(MODEL_PATHS['yolosam']['sam'])
            sam_path.parent.mkdir(exist_ok=True)

            if not sam_path.exists():
                print("  Downloading EfficientSAM weights...")
                import urllib.request
                urllib.request.urlretrieve(
                    'https://github.com/yformer/EfficientSAM/raw/main/weights/efficient_sam_vitt.pt',
                    str(sam_path)
                )

            efficientsam = build_efficient_sam_vitt()
            efficientsam.to(DEVICE).eval()

            print(f"✓ YOLO-SAM loaded successfully")
            return {'yolo': yolo_model, 'sam': efficientsam}

        except ImportError:
            print("⚠️  EfficientSAM not installed. Install with: pip install git+https://github.com/yformer/EfficientSAM.git")
            return {'yolo': yolo_model, 'sam': None}

    except Exception as e:
        print(f"✗ Failed to load YOLO-SAM: {e}")
        return None


def initialize_models():
    """Initialize all available models"""
    global models, car_detector

    print("="*80)
    print("INITIALIZING MODELS")
    print("="*80)
    print()

    # Load car detector for pre-filtering (COCO YOLOv11n)
    print("Loading car detector (pre-filter)...")
    try:
        from ultralytics import YOLO
        car_detector = YOLO('yolo11n.pt')  # Lightweight, pretrained on COCO
        print("✓ Car detector loaded (YOLOv11n COCO)")
    except Exception as e:
        print(f"⚠️  Could not load car detector: {e}")
        car_detector = None
    print()

    # Try to load each model
    model_loaders = {
        'maskrcnn': lambda: load_mmdet_model('maskrcnn'),
        'htc': lambda: load_mmdet_model('htc'),
        'yolact': lambda: load_mmdet_model('yolact'),
        'yolosam': load_yolosam_model
    }

    for name, loader in model_loaders.items():
        models[name] = loader()
        print()

    # Summary
    available = [name for name, model in models.items() if model is not None]
    print("="*80)
    print(f"LOADED MODELS: {', '.join(available) if available else 'None'}")
    print(f"CAR DETECTOR: {'Enabled' if car_detector else 'Disabled'}")
    print("="*80)
    print()


# ============================================================================
# INFERENCE FUNCTIONS
# ============================================================================

def check_car_in_image(image_np, conf_threshold=0.4):
    """
    Pre-filter: Check if there's a car in the image using COCO YOLO detector
    Returns: (has_car: bool, confidence: float)

    COCO class ID:
    - 2: car (ONLY)
    """
    if car_detector is None:
        # If car detector not loaded, allow all images (no filtering)
        return True, 1.0

    try:
        results = car_detector.predict(image_np, conf=conf_threshold, verbose=False)

        CAR_CLASS_ID = 2  # COCO class 2 = car

        for result in results:
            if result.boxes is None or len(result.boxes) == 0:
                continue

            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0].cpu().item())
                conf = box.conf[0].cpu().item()

                if cls == CAR_CLASS_ID:
                    print(f"[CAR DETECTOR] ✓ Detected car (confidence: {conf:.3f})")
                    return True, conf

        print(f"[CAR DETECTOR] ✗ No car detected in image")
        return False, 0.0

    except Exception as e:
        print(f"[CAR DETECTOR] Error: {e}")
        return True, 1.0  # On error, allow image through


def run_mmdet_inference(model, image_np, conf_threshold=0.5):
    """Run inference with MMDetection models"""
    from mmdet.apis import inference_detector

    # Run inference
    result = inference_detector(model, image_np)

    # Extract masks and scores
    if hasattr(result, 'pred_instances'):
        # MMDet 3.x format
        instances = result.pred_instances
        masks = instances.masks.cpu().numpy() if len(instances) > 0 else np.array([])
        scores = instances.scores.cpu().numpy() if len(instances) > 0 else np.array([])
        labels = instances.labels.cpu().numpy() if len(instances) > 0 else np.array([])
    else:
        # MMDet 2.x format
        masks = result[1] if len(result) > 1 else []
        scores = result[0][:, -1] if len(result[0]) > 0 else np.array([])
        labels = result[0][:, -2].astype(int) if len(result[0]) > 0 else np.array([])

    # DEBUG: Print detected classes
    if len(labels) > 0:
        print(f"\n[MMDET DEBUG] Detected {len(labels)} objects BEFORE confidence filter:")
        for i, (label, score) in enumerate(zip(labels, scores)):
            class_name = CLASS_NAMES[int(label)] if int(label) < len(CLASS_NAMES) else f"ClassID-{int(label)}"
            print(f"  [{i+1}] Class {int(label)}: {class_name} (confidence: {score:.3f})")

    # Filter by confidence
    if len(scores) > 0:
        valid_idx = scores >= conf_threshold
        masks = masks[valid_idx]
        scores = scores[valid_idx]
        labels = labels[valid_idx]

        print(f"[MMDET DEBUG] AFTER confidence filter (>={conf_threshold}): {len(labels)} objects kept\n")

    return masks, scores, labels


def run_yolosam_inference(model_dict, image_np, conf_threshold=0.5):
    """Run inference with YOLO-SAM hybrid"""
    yolo_model = model_dict['yolo']
    sam_model = model_dict.get('sam')

    h, w = image_np.shape[:2]

    # Run YOLO detection
    results = yolo_model.predict(image_np, conf=conf_threshold, iou=0.7, verbose=False)

    masks_list = []
    scores_list = []
    labels_list = []

    # DEBUG: Print YOLO detections
    print(f"\n[YOLO-SAM DEBUG] Running inference with conf_threshold={conf_threshold}")

    if sam_model is None:
        # Use YOLO segmentation masks only
        for result in results:
            if result.masks is not None and len(result.masks) > 0:
                masks = result.masks.data.cpu().numpy()
                scores = result.boxes.conf.cpu().numpy()
                labels = result.boxes.cls.cpu().numpy().astype(int) + 1  # Convert to 1-based

                # DEBUG: Print detections
                print(f"[YOLO-SAM DEBUG] Detected {len(labels)} objects:")
                for i, (label, score) in enumerate(zip(labels, scores)):
                    class_name = CLASS_NAMES[int(label)] if int(label) < len(CLASS_NAMES) else f"ClassID-{int(label)}"
                    print(f"  [{i+1}] Class {int(label)}: {class_name} (confidence: {score:.3f})")
                print()

                # Resize masks to original size
                resized_masks = []
                for mask in masks:
                    resized = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
                    resized_masks.append(resized > 0.5)

                return np.array(resized_masks), scores, labels
    else:
        # Use SAM for better masks
        from torchvision import transforms

        image_tensor = transforms.ToTensor()(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB))

        detection_count = 0
        for result in results:
            if result.boxes is None or len(result.boxes) == 0:
                continue

            boxes = result.boxes
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().item()
                cls = int(box.cls[0].cpu().item())
                category_id = cls + 1  # Convert to 1-based

                detection_count += 1
                class_name = CLASS_NAMES[category_id] if category_id < len(CLASS_NAMES) else f"ClassID-{category_id}"
                print(f"  [{detection_count}] Class {category_id}: {class_name} (confidence: {conf:.3f})")

                # YOLOv11 already returns boxes in original resolution
                x1, y1, x2, y2 = xyxy[0], xyxy[1], xyxy[2], xyxy[3]

                # Use bbox as prompt for SAM
                input_points = torch.tensor([[[[x1, y1], [x2, y2]]]]).to(DEVICE)
                input_labels = torch.tensor([[[2, 3]]]).to(DEVICE)

                with torch.no_grad():
                    predicted_logits, predicted_iou = sam_model(
                        image_tensor[None, ...].to(DEVICE),
                        input_points,
                        input_labels,
                    )

                # Get best mask
                sorted_ids = torch.argsort(predicted_iou, dim=-1, descending=True)
                predicted_logits = torch.take_along_dim(
                    predicted_logits, sorted_ids[..., None, None], dim=2
                )
                mask = torch.ge(predicted_logits[0, 0, 0, :, :], 0).cpu().numpy()

                masks_list.append(mask)
                scores_list.append(conf)
                labels_list.append(category_id)

        if detection_count > 0:
            print(f"[YOLO-SAM DEBUG] Total detections: {detection_count}\n")

    if len(masks_list) == 0:
        return np.array([]), np.array([]), np.array([])

    return np.array(masks_list), np.array(scores_list), np.array(labels_list)


def create_combined_mask(masks, labels, image_shape, method='method1'):
    """
    Combine multiple instance masks into single binary mask

    Args:
        masks: Instance masks from model
        labels: Class labels for each mask (1-based indexing)
        image_shape: Target image shape (h, w)
        method: 'method1' (direct wrappable) or 'method2' (car minus unwrappable)
    """
    h, w = image_shape[:2]
    combined = np.zeros((h, w), dtype=np.uint8)

    if method == 'method1':
        # Method 1: Direct wrappable filtering (11 classes)
        for mask, label in zip(masks, labels):
            if label in WRAPPABLE_CLASSES:
                if mask.shape != (h, w):
                    mask = cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_LINEAR)
                combined = np.logical_or(combined, mask > 0.5)

    return combined.astype(np.uint8) * 255


def create_method2_mask(image_np, masks, labels):
    """
    Method 2: Car mask minus unwrappable parts
    Uses rembg to get full car, then subtracts unwrappable parts

    Args:
        image_np: Original image (BGR)
        masks: Instance masks from model
        labels: Class labels for each mask (1-based indexing)

    Returns:
        Combined wrappable mask (uint8, 0-255)
    """
    try:
        from rembg import remove
    except ImportError:
        print("⚠️  rembg not installed. Falling back to Method 1")
        return create_combined_mask(masks, labels, image_np.shape, method='method1')

    h, w = image_np.shape[:2]

    # Get car mask using rembg
    image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
    car_mask = remove(image_rgb, only_mask=True)

    if isinstance(car_mask, Image.Image):
        car_mask = np.array(car_mask)

    car_mask = (car_mask > 128).astype(np.uint8)

    # Build unwrappable mask from detected parts
    unwrappable_mask = np.zeros((h, w), dtype=bool)

    if len(masks) > 0:
        for mask, label in zip(masks, labels):
            if label in UNWRAPPABLE_CLASSES:
                if mask.shape[:2] != (h, w):
                    mask_resized = cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_LINEAR)
                else:
                    mask_resized = mask
                unwrappable_mask = np.logical_or(unwrappable_mask, mask_resized > 0.5)

    # Subtract unwrappable from car mask
    wrappable_mask = car_mask & (~unwrappable_mask.astype(np.uint8))

    return (wrappable_mask * 255).astype(np.uint8)


def apply_hsv_color(image_np, mask_np, target_color_hex):
    """Apply HSV color transformation to masked regions ONLY"""
    # Convert hex to RGB
    target_color_hex = target_color_hex.lstrip('#')
    target_r = int(target_color_hex[0:2], 16)
    target_g = int(target_color_hex[2:4], 16)
    target_b = int(target_color_hex[4:6], 16)

    # Convert target color to HSV
    target_rgb = np.uint8([[[target_r, target_g, target_b]]])
    target_hsv = cv2.cvtColor(target_rgb, cv2.COLOR_RGB2HSV)[0, 0]
    target_h, target_s, target_v = target_hsv

    # Check if image has alpha channel
    has_alpha = len(image_np.shape) == 3 and image_np.shape[2] == 4

    # Work with BGR (strip alpha if present)
    if has_alpha:
        result = image_np.copy()
        image_bgr = image_np[:, :, :3]  # Strip alpha for processing
    else:
        result = image_np.copy()
        image_bgr = image_np

    # Convert to HSV for processing
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    image_hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV).astype(np.float32)

    # Apply color ONLY to masked regions
    mask_bool = mask_np > 128
    image_hsv[mask_bool, 0] = target_h  # Hue
    image_hsv[mask_bool, 1] = min(target_s * 1.1, 255)  # Saturation
    # Keep original Value to preserve lighting

    # Convert back to BGR
    image_hsv = np.clip(image_hsv, 0, 255).astype(np.uint8)
    colored_rgb = cv2.cvtColor(image_hsv, cv2.COLOR_HSV2RGB)
    colored_bgr = cv2.cvtColor(colored_rgb, cv2.COLOR_RGB2BGR)

    # Only apply masked pixels to result (only BGR channels)
    result[mask_bool, :3] = colored_bgr[mask_bool]

    return result


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """Serve static files"""
    return send_from_directory('.', path)


@app.route('/api/models', methods=['GET'])
def get_available_models():
    """Get list of available models and methods"""
    available_models = []

    model_info = {
        'maskrcnn': {'name': 'Mask R-CNN', 'speed': 'Slow (5-10s)', 'quality': 'High'},
        'htc': {'name': 'HTC', 'speed': 'Very Slow (10-30s)', 'quality': 'Very High'},
        'yolact': {'name': 'YOLACT', 'speed': 'Fast (1-3s)', 'quality': 'Good'},
        'yolosam': {'name': 'YOLO-SAM', 'speed': 'Moderate (3-8s)', 'quality': 'High'}
    }

    for model_id, model in models.items():
        if model is not None:
            info = model_info.get(model_id, {})
            available_models.append({
                'id': model_id,
                'name': info.get('name', model_id.upper()),
                'speed': info.get('speed', 'Unknown'),
                'quality': info.get('quality', 'Unknown')
            })

    # Available filtering methods
    methods = [
        {
            'id': 'method1',
            'name': 'Direct Wrappable',
            'description': 'Filter only wrappable parts (11 classes)',
            'speed': 'Fast'
        },
        {
            'id': 'method2',
            'name': 'Car Minus Unwrappable',
            'description': 'Full car mask minus unwrappable parts (uses rembg)',
            'speed': 'Slower (background removal)'
        }
    ]

    return jsonify({
        'models': available_models,
        'methods': methods
    })


@app.route('/api/segment', methods=['POST'])
def segment_image():
    """Generate segmentation mask"""
    try:
        data = request.json

        # Get parameters
        image_data = data.get('image')  # Base64 encoded
        model_name = data.get('model', 'yolact')
        method = data.get('method', 'method1')  # Default to Method 1
        conf_threshold = float(data.get('confidence', 0.5))
        use_car_detector = data.get('use_car_detector', False)  # Default: OFF (show pure model results)

        # Validate model
        if model_name not in models or models[model_name] is None:
            return jsonify({'error': f'Model {model_name} not available'}), 400

        # Validate method
        if method not in ['method1', 'method2']:
            return jsonify({'error': f'Invalid method: {method}'}), 400

        # Decode image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        image_pil = Image.open(BytesIO(image_bytes))
        image_np = np.array(image_pil)

        # Convert to BGR for OpenCV and ensure 3 channels
        if len(image_np.shape) == 3:
            if image_np.shape[2] == 4:
                # RGBA to BGR (strip alpha channel)
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
            elif image_np.shape[2] == 3:
                # RGB to BGR
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        elif len(image_np.shape) == 2:
            # Grayscale to BGR
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)

        # PRE-FILTER: Check if image contains a car (only if enabled)
        if use_car_detector:
            has_car, car_conf = check_car_in_image(image_np, conf_threshold=0.4)
            if not has_car:
                return jsonify({
                    'error': 'No car detected in image',
                    'message': 'Please upload an image containing a car.',
                    'suggestion': 'Make sure the car is clearly visible in the image.'
                }), 400
        else:
            print("[CAR DETECTOR] Disabled - Showing pure model results")

        # Run inference
        if model_name in ['maskrcnn', 'htc', 'yolact']:
            masks, scores, labels = run_mmdet_inference(models[model_name], image_np, conf_threshold)
        elif model_name == 'yolosam':
            masks, scores, labels = run_yolosam_inference(models[model_name], image_np, conf_threshold)
        else:
            return jsonify({'error': 'Invalid model'}), 400

        # Create combined binary mask based on method
        if len(masks) > 0:
            if method == 'method1':
                combined_mask = create_combined_mask(masks, labels, image_np.shape, method='method1')
            elif method == 'method2':
                combined_mask = create_method2_mask(image_np, masks, labels)
        else:
            combined_mask = np.zeros(image_np.shape[:2], dtype=np.uint8)

        # Convert mask to base64
        _, mask_encoded = cv2.imencode('.png', combined_mask)
        mask_base64 = base64.b64encode(mask_encoded).decode('utf-8')

        return jsonify({
            'success': True,
            'mask': f'data:image/png;base64,{mask_base64}',
            'num_instances': len(masks),
            'model': model_name,
            'method': method
        })

    except Exception as e:
        print(f"Error in segment_image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/colorize', methods=['POST'])
def colorize_image():
    """Apply color to segmented image"""
    try:
        data = request.json

        # Get parameters
        image_data = data.get('image')  # Base64 encoded
        mask_data = data.get('mask')    # Base64 encoded
        color_hex = data.get('color', '#dc2626')

        # Decode image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        image_pil = Image.open(BytesIO(image_bytes))
        image_np = np.array(image_pil)

        # Convert to BGR for OpenCV and ensure 3 channels
        if len(image_np.shape) == 3:
            if image_np.shape[2] == 4:
                # RGBA to BGR (strip alpha channel)
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
            elif image_np.shape[2] == 3:
                # RGB to BGR
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        elif len(image_np.shape) == 2:
            # Grayscale to BGR
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)

        # Decode mask
        mask_bytes = base64.b64decode(mask_data.split(',')[1])
        mask_pil = Image.open(BytesIO(mask_bytes))
        mask_np = np.array(mask_pil)

        # Ensure mask is single channel
        if len(mask_np.shape) == 3:
            mask_np = cv2.cvtColor(mask_np, cv2.COLOR_RGB2GRAY)

        # Apply HSV color transformation
        result_np = apply_hsv_color(image_np, mask_np, color_hex)

        # Convert back to RGB for frontend
        result_rgb = cv2.cvtColor(result_np, cv2.COLOR_BGR2RGB)

        # Encode result
        result_pil = Image.fromarray(result_rgb)
        buffered = BytesIO()
        result_pil.save(buffered, format='PNG')
        result_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return jsonify({
            'success': True,
            'result': f'data:image/png;base64,{result_base64}'
        })

    except Exception as e:
        print(f"Error in colorize_image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Initialize models on startup
    initialize_models()

    # Run Flask server
    print("="*80)
    print("STARTING FLASK SERVER")
    print("="*80)
    print()
    print("Server running at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print()

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
