from app.db.mongodb import client, database
from pymongo.errors import PyMongoError

def main():
    try:
        client.admin.command("ping")
        print("MongoDB connection succesful")
        print(f"Database:{database.name}")
    except PyMongoError as error:
        print("MongoDB connection failed")
        print(error)
    finally:
        client.close()

if __name__ == "__main__":
    main()