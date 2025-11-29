import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import torch

model = SentenceTransformer('all-MiniLM-L6-v2')

def encode_texts(text_list):
    with torch.no_grad():
        embeddings = model.encode(text_list, convert_to_tensor=True, normalize_embeddings=True)
    return embeddings

def compute_iou(interval1, interval2):
    start1, end1 = interval1
    start2, end2 = interval2
    inter = max(0, min(end1, end2) - max(start1, start2))
    union = max(end1, end2) - min(start1, start2)
    return inter / union if union > 0 else 0.0

def compute_similarity_matrix(gt_step_texts, pred_step_texts, encoder):
    gt_vecs = encoder(gt_step_texts).detach().cpu().numpy()
    pred_vecs = encoder(pred_step_texts).detach().cpu().numpy()
    return cosine_similarity(gt_vecs, pred_vecs)

def match_steps_hungarian(similarity_matrix, threshold):
    cost_matrix = 1 - similarity_matrix
    gt_indices, pred_indices = linear_sum_assignment(cost_matrix)
    matches = []
    for i, j in zip(gt_indices, pred_indices):
        if similarity_matrix[i][j] >= threshold:
            matches.append((i, j))
    return matches

def evaluate_prediction(gt_steps, pred_steps, encoder, sim_threshold=0.5, iou_threshold=0.3):
    S = compute_similarity_matrix([s['text'] for s in gt_steps], [s['text'] for s in pred_steps], encoder)
    matches = match_steps_hungarian(S, sim_threshold)

    n_gt = len(gt_steps)
    matched_gt = set(i for i, _ in matches)
    matched_pred = set(j for _, j in matches)

    errors = {
        'SM_vid': n_gt - len(matched_gt),
        'SH_vid': len(pred_steps) - len(matched_pred),
        'SO_vid': 0,
        'SFP_vid': 0,
        'SFN_vid': 0,
        'MTGS_vid': 0
    }

    cnt = 0

    for gt_idx, pred_idx in matches:
        if gt_idx != pred_idx:
            errors['SO_vid'] += 1

        gt = gt_steps[gt_idx]
        pred = pred_steps[pred_idx]

        pred_vid_step = []
        gt_vid_step = []

        for pred_vid, pred_start, pred_end in pred['groundings']:
            matched = False
            for gt_vid, gt_start, gt_end in gt['groundings']:
                cnt += 1
                if pred_vid == gt_vid:
                    matched = True
                    iou = compute_iou((pred_start, pred_end), (gt_start, gt_end))
                    errors['MTGS_vid'] += iou

        for pred_vid, _, _ in pred['groundings']:
            pred_vid_step.append(pred_vid)
        
        for gt_vid, _, _ in gt['groundings']:
            gt_vid_step.append(gt_vid)

        pred_vid_step, gt_vid_step = set(pred_vid_step), set(gt_vid_step)
        errors['SFP_vid'] += len(set(pred_vid_step) - set(gt_vid_step))
        errors['SFN_vid'] += len(set(gt_vid_step) - set(pred_vid_step))

    errors['MTGS_vid'] = errors['MTGS_vid'] / cnt
    errors['cnt'] = cnt

    return errors