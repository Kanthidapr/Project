from fastapi import FastAPI
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 MongoDB ของคุณ
uri = ""
client = MongoClient(uri)

db = client["finance"]
transactions = db["transactions"]

# 📌 ดึงข้อมูลทั้งหมด
@app.get("/transactions")
def get_transactions():
    data = []
    for t in transactions.find():
        t["_id"] = str(t["_id"])
        data.append(t)
    return data

# 📌 เพิ่มข้อมูล
@app.post("/transactions")
def add_transaction(item: dict):
    transactions.insert_one(item)
    return {"message": "added"}

# 📌 ลบข้อมูล
@app.delete("/transactions/{tid}")
def delete_transaction(tid: str):
    result = transactions.delete_one({"_id": tid})
    if result.deleted_count == 0:
        return {"message": "not found"}
    return {"message": "deleted"}

@app.post("/transactions")
def add_transaction(data: dict):
    data["date"] = datetime.now().strftime("%d/%m")
    transactions.insert_one(data)
    return {"message": "added"}