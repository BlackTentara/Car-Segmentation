_base_ = '../yolact/yolact_r50_1xb8-55e_coco.py'

# Define the 22 classes - MUST match training exactly
classes = ('carros', 'Back-bumper', 'Back-door', 'Back-wheel', 'Back-window','Back-windshield',
           'Fender','Front-bumper', 'Front-door', 'Front-wheel', 'Front-window', 'Grille',
           'Headlight','Hood','License-plate','Mirror', 'Quarter-panel', 'Rocker-panel', 'Roof',
            'Tail-light', 'Trunk','Windshield')

# Number of classes
num_classes = len(classes)

# Update model
model = dict(
    bbox_head=dict(num_classes=num_classes),
    mask_head=dict(num_classes=num_classes)
)

# Test settings
test_cfg = dict(
    nms_pre=1000,
    min_bbox_size=0,
    score_thr=0.5,
    mask_thr=0.5,
    max_per_img=100,
    nms=dict(type='nms', iou_threshold=0.5)
)

# Dataset settings
dataset_type = 'CocoDataset'
data_root = 'data/coco/'

test_dataloader = dict(
    batch_size=1,
    dataset=dict(
        type=dataset_type,
        metainfo=dict(classes=classes),
        ann_file='annotations/instances_val2017.json',
        data_prefix=dict(img='val2017/')
    )
)

test_evaluator = dict(
    type='CocoMetric',
    ann_file=data_root + 'annotations/instances_val2017.json',
    metric=['bbox', 'segm'],
    format_only=False
)
