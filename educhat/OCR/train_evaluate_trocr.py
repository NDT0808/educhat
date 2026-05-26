import os
import time
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import TrOCRProcessor, VisionEncoderDecoderModel, Seq2SeqTrainer, Seq2SeqTrainingArguments
from transformers import default_data_collator
import evaluate

# ==========================================
# 1. DATASET CUSTOM (ĐỌC ẢNH VÀ LABELS TỪ CSV)
# ==========================================
class OCRDataset(Dataset):
    def __init__(self, root_dir, df, processor, max_target_length=128):
        self.root_dir = root_dir
        self.df = df
        self.processor = processor
        self.max_target_length = max_target_length

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        file_name = self.df['file_name'][idx]
        text = str(self.df['text'][idx])
        
        # Mở ảnh và chuyển sang RGB
        image_path = os.path.join(self.root_dir, file_name)
        image = Image.open(image_path).convert("RGB")
        
        # Tiền xử lý ảnh (Resize, Normalize cho ViT Encoder)
        pixel_values = self.processor(image, return_tensors="pt").pixel_values
        
        # Tiền xử lý Text (Tokenization cho RoBERTa Decoder)
        labels = self.processor.tokenizer(
            text, 
            padding="max_length", 
            max_length=self.max_target_length,
            truncation=True
        ).input_ids
        
        # Đưa padding (-100) để model không tính Loss ở các khoảng trống
        labels = [label if label != self.processor.tokenizer.pad_token_id else -100 for label in labels]

        return {"pixel_values": pixel_values.squeeze(), "labels": torch.tensor(labels)}

# ==========================================
# 2. HÀM TÍNH TOÁN METRICS (CER, WER, ACCURACY) CHO BÁO CÁO NCKH
# ==========================================
cer_metric = evaluate.load("cer")
wer_metric = evaluate.load("wer")

def compute_metrics(pred, processor):
    labels_ids = pred.label_ids
    pred_ids = pred.predictions

    # Decode dự đoán
    pred_str = processor.batch_decode(pred_ids, skip_special_tokens=True)
    
    # Loại bỏ -100 trước khi decode labels thật
    labels_ids[labels_ids == -100] = processor.tokenizer.pad_token_id
    label_str = processor.batch_decode(labels_ids, skip_special_tokens=True)

    # Tính CER và WER
    cer = cer_metric.compute(predictions=pred_str, references=label_str)
    wer = wer_metric.compute(predictions=pred_str, references=label_str)
    
    # Tính Accuracy (Khớp 100% từng chữ)
    exact_match = sum([1 if p.strip() == l.strip() else 0 for p, l in zip(pred_str, label_str)])
    accuracy = exact_match / len(label_str)

    return {"cer": cer, "wer": wer, "accuracy": accuracy}

def main():
    print("=== BẮT ĐẦU QUÁ TRÌNH HUẤN LUYỆN (TRAINING) ===")
    
    # Khởi tạo mô hình
    MODEL_NAME = "microsoft/trocr-base-printed"
    processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
    model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)

    model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.vocab_size = model.config.decoder.vocab_size
    
    # Setup metrics function closure
    def compute_metrics_closure(pred):
        return compute_metrics(pred, processor)

    # Đọc dữ liệu
    train_df = pd.read_csv("train.csv")
    test_df = pd.read_csv("test.csv")
    
    # Lọc bỏ các dòng bị lỗi (ảnh không tồn tại thực tế)
    train_df = train_df[train_df['file_name'].apply(lambda x: os.path.exists(os.path.join("data", x)))].reset_index(drop=True)
    test_df = test_df[test_df['file_name'].apply(lambda x: os.path.exists(os.path.join("data", x)))].reset_index(drop=True)
    
    print(f"Số lượng ảnh Train hợp lệ: {len(train_df)}")
    print(f"Số lượng ảnh Test hợp lệ: {len(test_df)}")

    train_dataset = OCRDataset(root_dir="data", df=train_df, processor=processor)
    eval_dataset = OCRDataset(root_dir="data", df=test_df, processor=processor)

    # Cấu hình huấn luyện
    training_args = Seq2SeqTrainingArguments(
        predict_with_generate=True,
        eval_strategy="epoch",
        per_device_train_batch_size=4,  # Có thể tăng lên 8 nếu GPU mạnh
        per_device_eval_batch_size=4,
        learning_rate=2e-5,
        weight_decay=0.01,
        fp16=torch.cuda.is_available(), # Dùng fp16 nếu có GPU
        output_dir="./trocr_results",
        num_train_epochs=3,             # NCKH nên để 10-20 epoch
        save_strategy="epoch",
        logging_steps=10,
        report_to="none" # Tắt wandb nếu không dùng
    )

    trainer = Seq2SeqTrainer(
        model=model,
        tokenizer=processor.image_processor,
        args=training_args,
        compute_metrics=compute_metrics_closure,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=default_data_collator,
    )

    # 1. BẮT ĐẦU TRAIN
    print("Đang huấn luyện mô hình. Quá trình này sẽ mất thời gian tùy thuộc vào GPU của bạn...")
    trainer.train()
    
    # Lưu mô hình
    model.save_pretrained("./my-final-trocr")
    processor.save_pretrained("./my-final-trocr")
    print("Đã lưu mô hình huấn luyện vào thư mục './my-final-trocr'!")

    # ==========================================
    # 3. ĐO LƯỜNG TỐC ĐỘ (FPS) SAU KHI TRAIN
    # ==========================================
    print("\n=== ĐO LƯỜNG CHỈ SỐ INFERENCE FPS (FRAMES PER SECOND) ===")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    
    eval_dataloader = DataLoader(eval_dataset, batch_size=1)
    
    start_time = time.time()
    total_samples = len(eval_dataset)
    
    # Đo tốc độ cho 50 ảnh để lấy FPS trung bình (tiết kiệm thời gian test)
    samples_to_test = min(50, total_samples)
    print(f"Đang chạy Inference trên {samples_to_test} ảnh để tính FPS...")
    
    with torch.no_grad():
        for i, batch in enumerate(eval_dataloader):
            if i >= samples_to_test:
                break
            pixel_values = batch["pixel_values"].to(device)
            _ = model.generate(pixel_values)
            
    end_time = time.time()
    total_time = end_time - start_time
    fps = samples_to_test / total_time
    
    print("-" * 50)
    print(f"BÁO CÁO KẾT QUẢ HIỆU NĂNG CHO NCKH:")
    print(f"- Tổng thời gian suy luận: {total_time:.2f} giây")
    print(f"- Số ảnh đã xử lý: {samples_to_test}")
    print(f"- Tốc độ (FPS): {fps:.2f} ảnh/giây")
    print(f"- Thiết bị chạy: {device}")
    print("-" * 50)
    print("Bạn hãy lấy các chỉ số CER, WER, Accuracy trong bảng Log ở phía trên và chỉ số FPS này để đưa vào Báo cáo nhé!")

if __name__ == "__main__":
    main()
