from pymongo.mongo_client import MongoClient

uri = "mongodb+srv://kanthidapr:Ku_00035@cluster0.budqfqh.mongodb.net/"

client = MongoClient(uri)

try:
    client.admin.command('ping')
    print("Connected to MongoDB!")

    db = client["finance"]
    transactions = db["transactions"]
    categories = db["categories"]

    while True:
        print("=== MENU ===")
        print("1: Show all transactions")
        print("2: Insert category")
        print("3: Insert transaction")
        print("4: Update transaction")
        print("5: Delete transaction")
        print("6: Exit")

        choice = int(input("Please choose: "))

        # SHOW ALL TRANSACTIONS
        if choice == 1:
            print(f"Found {transactions.count_documents({})} records")
            for t in transactions.find():
                print(t)

        # INSERT CATEGORY
        elif choice == 2:
            cid = input("Category ID: ")
            cname = input("Category name (shopping/invest/saving): ")

            try:
                categories.insert_one({
                    "_id": cid,
                    "category_name": cname
                })
                print("Category inserted!")
            except Exception as e:
                print(e)

        # INSERT TRANSACTION
        elif choice == 3:
            tid = input("Transaction ID: ")
            date = input("Date (YYYY-MM-DD): ")
            ttype = input("Type (income/expense): ")
            cid = input("Category ID: ")
            amount = float(input("Amount: "))

            try:
                transactions.insert_one({
                    "_id": tid,
                    "date": date,
                    "type": ttype,
                    "category_id": cid,
                    "amount": amount
                })
                print("Transaction inserted!")
            except Exception as e:
                print(e)

        # UPDATE TRANSACTION
        elif choice == 4:
            tid = input("Transaction ID to update: ")
            new_date = input("New Date: ")
            new_type = input("New Type: ")
            new_cid = input("New Category ID: ")
            new_amount = float(input("New Amount: "))

            result = transactions.update_one(
                {"_id": tid},
                {"$set": {
                    "date": new_date,
                    "type": new_type,
                    "category_id": new_cid,
                    "amount": new_amount
                }}
            )

            if result.matched_count == 0:
                print("No record found")
            else:
                print("Transaction updated!")

        # DELETE TRANSACTION
        elif choice == 5:
            tid = input("Transaction ID to delete: ")
            result = transactions.delete_one({"_id": tid})

            if result.deleted_count == 0:
                print("No record found")
            else:
                print("Deleted successfully!")

        elif choice == 6:
            print("BYE!")
            break

except Exception as e:
    print(e)

finally:
    client.close()