from fastapi import FastAPI, HTTPException
from pymongo import MongoClient, ReturnDocument
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # อนุญาตทุกเว็บ (ใช้ตอน deploy ก่อน)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DB ----------------
uri = "mongodb+srv://kanthidapr:kU_00035@cluster0.budqfqh.mongodb.net/finance?retryWrites=true&w=majority"
client = MongoClient(uri)

db = client["finance"]
transactions = db["transactions"]
wallets = db["wallets"]

# ---------------- MODELS ----------------
class Transaction(BaseModel):
    title: str
    amount: float
    wallet: str
    type: str
    date: str = None

# ---------------- GET ----------------
@app.get("/transactions")
def get_transactions():
    data = []
    for t in transactions.find():
        t["_id"] = str(t["_id"])
        data.append(t)
    return data

# ---------------- ADD ----------------
@app.post("/transactions")
def add_transaction(data: Transaction):
    wallet = wallets.find_one({"name": data.wallet})
    if not wallet:
        raise HTTPException(status_code=404, detail="wallet not found")

    # ✅ FIX: กำหนด + / - ที่ backend
    amount = abs(data.amount)
    if data.type == "expense":
        amount = -amount

    item = data.dict()
    item["amount"] = amount
    item["date"] = datetime.now().strftime("%d/%m")

    result = transactions.insert_one(item)

    wallets.update_one(
        {"name": data.wallet},
        {"$inc": {"balance": amount}}  # ✅ ใช้ amount ที่ fix แล้ว
    )

    return {"id": str(result.inserted_id)}

# ---------------- UPDATE ----------------
@app.put("/transactions/{tid}")
def update_transaction(tid: str, data: Transaction):
    try:
        obj_id = ObjectId(tid)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")

    t = transactions.find_one({"_id": obj_id})
    if not t:
        raise HTTPException(status_code=404, detail="not found")

    # ลบยอดเก่า
    wallets.update_one(
        {"name": t["wallet"]},
        {"$inc": {"balance": -t["amount"]}}
    )

    # ✅ FIX: คำนวณ amount ใหม่
    amount = abs(data.amount)
    if data.type == "expense":
        amount = -amount

    # เพิ่มยอดใหม่
    wallets.update_one(
        {"name": data.wallet},
        {"$inc": {"balance": amount}}
    )

    transactions.update_one(
        {"_id": obj_id},
        {"$set": {
            "title": data.title,
            "amount": amount,
            "wallet": data.wallet,
            "type": data.type,
            "date": data.date
        }}
    )

    return {"message": "updated"}

# ---------------- DELETE ----------------
@app.delete("/transactions/{tid}")
def delete_transaction(tid: str):
    try:
        obj_id = ObjectId(tid)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")

    t = transactions.find_one({"_id": obj_id})
    if not t:
        raise HTTPException(status_code=404, detail="not found")

    wallets.update_one(
        {"name": t["wallet"]},
        {"$inc": {"balance": -t["amount"]}}
    )

    transactions.delete_one({"_id": obj_id})

    return {"message": "deleted"}

# ---------------- WALLET ----------------

class Wallet(BaseModel):
    name: str
    balance: float = 0


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


@app.delete("/wallets/{name}")
def delete_wallet(name: str):
    wallet = wallets.find_one({"name": name})
    if not wallet:
        raise HTTPException(status_code=404, detail="wallet not found")

    transactions.delete_many({"wallet": name})
    wallets.delete_one({"name": name})

    return {"message": "deleted"}