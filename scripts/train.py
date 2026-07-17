import os
import pickle
import shutil
from datetime import date, datetime
import sys

# Thêm thư mục ai vào sys.path để có thể import ai_service
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ai_path = os.path.join(root_dir, "ai")
if ai_path not in sys.path:
    sys.path.append(ai_path)

from ai_service import datagen, forecasting, pricing

def main():
    print("=== Training Forecasting Model ===")
    
    # 1. Tạo thư mục ai/models/ nếu chưa tồn tại
    models_dir = os.path.join(ai_path, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    versioned_model_path = os.path.join(models_dir, f"model_{timestamp}.pkl")
    default_model_path = os.path.join(models_dir, "model.pkl")
    
    # 2. Sinh dữ liệu mô phỏng lịch sử (ví dụ: 100 ngày để chạy nhanh và hội tụ tốt)
    print("[TRAIN] Generating 100 days of simulation history...")
    sim = datagen.simulate(start=date(2024, 1, 1), days=100)
    hist = sim["history"]
    
    # 3. Huấn luyện mô hình Forecaster
    print("[TRAIN] Fitting Forecaster models (point and quantiles)...")
    fc = forecasting.Forecaster()
    fc.fit(hist)
    
    # 4. Ước lượng độ co giãn nhu cầu (elasticity)
    print("[TRAIN] Estimating price elasticity...")
    eps = pricing.estimate_elasticity(hist)
    
    # 5. Lưu mô hình và tham số
    print(f"[TRAIN] Saving model to {versioned_model_path}...")
    bundle = {
        "forecaster": fc,
        "eps": eps
    }
    with open(versioned_model_path, "wb") as f:
        pickle.dump(bundle, f)
        
    print(f"[TRAIN] Copying latest model to {default_model_path}...")
    shutil.copy2(versioned_model_path, default_model_path)
        
    print("[TRAIN] Training completed successfully!")

if __name__ == "__main__":
    main()
