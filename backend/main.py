from fastapi import FastAPI, HTTPException
from pymongo import MongoClient, ReturnDocument
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

# ---------------- DB ----------------
uri = "mongodb+srv://kanthidapr:kU_00035@cluster0.budqfqh.mongodb.net/finance?retryWrites=true&w=majority"
client = MongoClient(uri)

db = client["finance"]
transactions = db["transactions"]
wallets = db["wallets"]
users = db["users"]
counters = db["counters"]

# ---------------- AUTO USER ID ----------------
def get_next_user_id():
    counter = counters.find_one_and_update(
        {"_id": "user_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return str(counter["seq"]).zfill(4)

# ---------------- MODELS ----------------
class Transaction(BaseModel):
    title: str
    amount: float
    wallet: str

class Wallet(BaseModel):
    name: str
    balance: float = 0

class User(BaseModel):
    username: str
    email: str
    password: str

class LoginData(BaseModel):
    username: str
    password: str

# ---------------- USER (SIGNUP) ----------------
@app.post("/users")
def create_user(user: User):

    if not user.username.strip() or not user.email.strip() or not user.password.strip():
        raise HTTPException(status_code=400, detail="All fields are required")

    if users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")

    if users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")

    user_id = get_next_user_id()

    new_user = user.dict()
    new_user["user_id"] = user_id

    users.insert_one(new_user)

    return {
        "message": "user created",
        "user_id": user_id
    }

# ---------------- LOGIN ----------------
@app.post("/login")
def login(data: LoginData):

    if not data.username.strip() or not data.password.strip():
        raise HTTPException(status_code=400, detail="All fields are required")

    user = users.find_one({"username": data.username})

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if user["password"] != data.password:
        raise HTTPException(status_code=400, detail="Wrong password")

    return {
        "message": "login success",
        "user_id": user["user_id"]
    }

@app.get("/users")
def get_users():
    data = []
    for u in users.find():
        u["_id"] = str(u["_id"])
        data.append(u)
    return data

# ---------------- WALLET ----------------
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

    return {"message": "wallet deleted"}

# ---------------- TRANSACTION ----------------
@app.get("/transactions")
def get_transactions():
    data = []
    for t in transactions.find():
        t["_id"] = str(t["_id"])
        data.append(t)
    return data

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

    wallets.update_one(
        {"name": t["wallet"]},
        {"$inc": {"balance": -t["amount"]}}
    )

    wallets.update_one(
        {"name": data.wallet},
        {"$inc": {"balance": data.amount}}
    )

    transactions.update_one(
        {"_id": ObjectId(tid)},
        {"$set": data.dict()}
    )

    return {"message": "updated"}

@app.delete("/transactions/{tid}")
def delete_transaction(tid: str):
    t = transactions.find_one({"_id": ObjectId(tid)})
    if not t:
        raise HTTPException(status_code=404, detail="not found")

    wallets.update_one(
        {"name": t["wallet"]},
        {"$inc": {"balance": -t["amount"]}}
    )

    transactions.delete_one({"_id": ObjectId(tid)})

    return {"message": "deleted"}