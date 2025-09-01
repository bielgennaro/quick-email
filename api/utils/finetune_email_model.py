import json
from datasets import load_dataset, Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
import torch
import os

MODEL_NAME = "google/gemma-3-270m" 
DATASET_PATH = "finetune_dataset.json"
OUTPUT_DIR = "finetuned_model"

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Preparar exemplos para o modelo
examples = []
for item in data:
    prompt = (
        f"Você é um assistente de e-mails. Leia o texto do e-mail e do anexo (se houver) e gere uma resposta adequada.\n"
        f"Texto do e-mail: \"{item['email_text']}\"\n"
    )
    if item["attachment_text"]:
        prompt += f"Conteúdo do anexo: \"{item['attachment_text']}\"\n"
    prompt += "Resposta: "
    full_text = prompt + item["response"]
    examples.append({"text": full_text})

dataset = Dataset.from_list(examples)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=512)

tokenized_dataset = dataset.map(tokenize_function, batched=True)

data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer, mlm=False
)

model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    overwrite_output_dir=True,
    num_train_epochs=5,
    per_device_train_batch_size=2,
    save_steps=10,
    save_total_limit=2,
    logging_steps=5,
    learning_rate=5e-5,
    fp16=torch.cuda.is_available(),
    report_to=[],
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
)

trainer.train()

model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"Fine-tuning concluído! Modelo salvo em {OUTPUT_DIR}")
