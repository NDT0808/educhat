# File: train_emotion.py (Bản có biểu đồ & Test trực tiếp)
import pandas as pd
import numpy as np
import torch
import os
import matplotlib.pyplot as plt
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from datasets import Dataset

# 1. Load dữ liệu
print("Đang nạp dữ liệu...")
df = pd.read_csv('emotion_data.csv')
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# 2. Tokenizer & Model
model_name = "vinai/phobert-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=64)

train_dataset = Dataset.from_pandas(train_df).map(tokenize_function, batched=True)
test_dataset = Dataset.from_pandas(test_df).map(tokenize_function, batched=True)

model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=4)

# Hàm tính toán chỉ số (Để vẽ biểu đồ và báo cáo)
history = {"loss": [], "eval_loss": [], "eval_accuracy": []}

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, predictions)
    
    # Xuất báo cáo chi tiết Precision, Recall, F1
    report = classification_report(labels, predictions, target_names=["Tích cực", "Trung tính", "Áp lực nhẹ", "Áp lực cao"])
    print("\n" + "="*20 + " BÁO CÁO KẾT QUẢ " + "="*20)
    print(report)
    
    history["eval_accuracy"].append(acc)
    return {"accuracy": acc}

# 3. Cấu hình huấn luyện
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=5, # Tăng lên 5 epoch để biểu đồ đẹp hơn
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    eval_strategy="epoch",
    save_strategy="no",
    logging_steps=10,
    fp16=True,
    optim='adamw_torch',
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    compute_metrics=compute_metrics,
)

# 4. Huấn luyện
print("Bắt đầu huấn luyện...")
train_result = trainer.train()

# 5. Vẽ biểu đồ kết quả
print("Đang tạo biểu đồ...")
plt.figure(figsize=(10, 5))
plt.plot(history["eval_accuracy"], label='Validation Accuracy', marker='o')
plt.title('Mô hình PhoBERT - Độ chính xác qua các Epoch')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)
plt.savefig('training_report.png')
print("Đã lưu biểu đồ vào file: training_report.png")

# 6. Lưu mô hình vào cả 2 nơi (Local và Backend)
save_paths = [
    "./models/emotion_v2",
    r"c:\Users\ASUS\Downloads\educhat\educhat\services\llm\models\emotion_v2"
]

for path in save_paths:
    os.makedirs(path, exist_ok=True)
    model.save_pretrained(path)
    tokenizer.save_pretrained(path)
    print(f"Đã lưu mô hình tại: {path}")

# 7. TEST TRỰC TIẾP TRONG SOURCE
print("\n" + "="*20 + " CHẠY THỬ NGAY TRONG SOURCE " + "="*20)
test_texts = [
    "Hôm nay mình rất vui vì làm được bài",
    "Môn này khó quá, mình lo lắng quá",
    "Mình muốn bỏ học vì quá bế tắc",
    "Cho mình hỏi lịch thi"
]

labels_map = {0: "Tích cực", 1: "Trung tính", 2: "Áp lực nhẹ", 3: "Áp lực cao"}
model.eval()

for text in test_texts:
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=64).to(model.device)
    with torch.no_grad():
        outputs = model(**inputs)
        prediction = torch.argmax(outputs.logits, dim=-1).item()
        print(f"Câu hỏi: {text} -> Kết quả: {labels_map[prediction]}")
