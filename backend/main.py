from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uri = "mongodb+srv://kanthidapr:kU_00035@cluster0.budqfqh.mongodb.net/finance?retryWrites=true&w=majority"
client = MongoClient(uri)

db = client["finance"]
transactions = db["transactions"]
wallets = db["wallets"]

class Transaction(BaseModel):
    title: str
    amount: float
    wallet: str

class Wallet(BaseModel):
    name: str
    balance: float = 0

# WALLET
@app.post("/wallets")
def create_wallet(data: Wallet):
    if wallets.find_one({"name": data.name}):
        raise HTTPException(status_code=400, detail="wallet exists")
    wallets.insert_one(data.dict())
    return {"message": "created"}

@app.get("/wallets")
def get_wallets():
    data = []
    for w in wallets.find():
        w["_id"] = str(w["_id"])
        data.append(w)
    return data

# TRANSACTION
@app.get("/transactions")
def get_transactions():
    data = []
    for t in transactions.find():
        t["_id"] = str(t["_id"])
        data.append(t)
    return data

@app.put("/transactions/{tid}")
def update_transaction(tid: str, data: Transaction):
    t = transactions.find_one({"_id": ObjectId(tid)})
    if not t:
        raise HTTPException(status_code=404, detail="not found")

    transactions.update_one(
        {"_id": ObjectId(tid)},
        {"$set": {
            "title": data.title,
            "amount": data.amount,
            "wallet": data.wallet
        }}
    )

    return {"message": "updated"}

@app.post("/transactions")
def add_transaction(data: Transaction):
    wallet = wallets.find_one({"name": data.wallet})
    if not wallet:
        raise HTTPException(status_code=404, detail="wallet not found")

    item = data.dict()
    item["date"] = datetime.now().strftime("%d/%m")

    result = transactions.insert_one(item)

    wallets.update_one(
        {"name": data.wallet},
        {"$inc": {"balance": data.amount}}
    )

    return {"id": str(result.inserted_id)}

@app.put("/transactions/{tid}")
def update_transaction(tid: str, data: Transaction):
    t = transactions.find_one({"_id": ObjectId(tid)})
    if not t:
        raise HTTPException(status_code=404, detail="not found")

    # ❗ คืนค่าเก่า
    wallets.update_one(
        {"name": t["wallet"]},
        {"$inc": {"balance": -t["amount"]}}
    )

    # ❗ เพิ่มค่าใหม่
    wallets.update_one(
        {"name": data.wallet},
        {"$inc": {"balance": data.amount}}
    )

    transactions.update_one(
        {"_id": ObjectId(tid)},
        {"$set": {
            "title": data.title,
            "amount": data.amount,
            "wallet": data.wallet
        }}
    )

    return {"message": "updated"}

@app.delete("/transactions/{tid}")
def delete_transaction(tid: str):
    t = transactions.find_one({"_id": ObjectId(tid)})
    if not t:
        raise HTTPException(status_code=404, detail="not found")

    # ❗ คืนเงินให้ wallet
    wallets.update_one(
        {"name": t["wallet"]},
        {"$inc": {"balance": -t["amount"]}}
    )

    # ❗ ลบ transaction
    transactions.delete_one({"_id": ObjectId(tid)})

    return {"message": "deleted"}

@app.delete("/wallets/{name}")
def delete_wallet(name: str):
    wallet = wallets.find_one({"name": name})
    if not wallet:
        raise HTTPException(status_code=404, detail="wallet not found")

    # ลบ transaction ที่อยู่ใน wallet นี้ทั้งหมด
    transactions.delete_many({"wallet": name})

    # ลบ wallet
    wallets.delete_one({"name": name})

    return {"message": "wallet deleted"}