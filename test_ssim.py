import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

def run_ssim(before_path, after_path, threshold=0.7):
    before = cv2.imread(before_path)
    after = cv2.imread(after_path)
    if before is None or after is None:
        print(f"Error loading images: {before_path}, {after_path}")
        return

    assert before.shape == after.shape, f"Shape mismatch: {before.shape} vs {after.shape}"

    before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

    score, diff_map = ssim(before_gray, after_gray, full=True)
    print(f"Overall SSIM similarity: {score:.4f}")

    diff_map = (1 - diff_map)
    diff_map = (diff_map * 255).astype("uint8")

    # Threshold: lower similarity (higher dissimilarity) = change
    _, change_mask = cv2.threshold(diff_map, int((1 - threshold) * 255), 255, cv2.THRESH_BINARY)

    kernel = np.ones((3, 3), np.uint8)
    change_mask = cv2.morphologyEx(change_mask, cv2.MORPH_OPEN, kernel)
    change_mask = cv2.morphologyEx(change_mask, cv2.MORPH_CLOSE, kernel)

    change_percent = (np.sum(change_mask == 255) / change_mask.size) * 100
    print(f"SSIM-based change detected (threshold={threshold}): {change_percent:.2f}% of area")

    overlay = after.copy()
    overlay[change_mask == 255] = [0, 0, 255]
    blended = cv2.addWeighted(after, 0.6, overlay, 0.4, 0)

    cv2.imwrite("ssim_change_mask.png", change_mask)
    cv2.imwrite("ssim_change_overlay.png", blended)
    print("Saved ssim_change_mask.png and ssim_change_overlay.png")

    # Also test sweep
    print("\n--- SSIM Sensitivity Sweep ---")
    for th in [0.50, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85]:
        _, mask = cv2.threshold(diff_map, int((1 - th) * 255), 255, cv2.THRESH_BINARY)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        pct = (np.sum(mask == 255) / mask.size) * 100
        print(f"  Threshold {th:.2f} (dissimilarity >= {int((1-th)*255):3d}/255): {pct:6.2f}% area changed")

if __name__ == "__main__":
    run_ssim("nagpur_before.png", "nagpur_after.png", threshold=0.7)
