from databases import Database
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table, delete

database_url = "postgresql://postgres:Konoplev27@localhost/microservice"
db = Database(database_url)


class Item(BaseModel):
    name: str
    description: str


metadata = MetaData()

items = Table(
    "items",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, index=True),
    Column("description", String),
)

engine = create_engine(database_url)
metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    return db


@app.get("/items", response_model=list)
async def read_items_api(db: Database = Depends(get_db)):
    try:
        await db.connect()
        query = items.select()
        items_list = await db.fetch_all(query)
        return [{"name": item["name"], "description": item["description"]} for item in items_list]
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
    finally:
        await db.disconnect()


@app.get("/items/{item_id}", response_model=Item)
async def read_item_by_id(item_id: int, db: Database = Depends(get_db)):
    try:
        await db.connect()
        query = items.select().where(items.c.id == item_id)
        item = await db.fetch_one(query)
        if item:
            return {"name": item["name"], "description": item["description"]}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
    finally:
        await db.disconnect()


@app.delete("/items", response_model=dict)
async def delete_all_items(db: Database = Depends(get_db)):
    try:
        await db.connect()

        query = delete(items)
        result = await db.execute(query)

        return {"message": "All items deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
    finally:
        await db.disconnect()


@app.delete("/items/{item_id}", response_model=dict)
async def delete_item_by_id(item_id: int, db: Database = Depends(get_db)):
    try:
        await db.connect()

        existing_item = await db.fetch_one(items.select().where(items.c.id == item_id))

        if existing_item is None:
            raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found")

        query = delete(items).where(items.c.id == item_id)
        result = await db.execute(query)

        return {"message": f"Item with id {item_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
    finally:
        await db.disconnect()


@app.post("/items", response_model=Item)
async def create_item(item: Item, db: Database = Depends(get_db)):
    try:
        await db.connect()

        query = items.insert().values(name=item.name, description=item.description)
        item_id = await db.execute(query)
        return {"id": item_id, **item.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
    finally:
        await db.disconnect()


@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item, db: Database = Depends(get_db)):
    try:
        await db.connect()

        existing_item = await db.fetch_one(items.select().where(items.c.id == item_id))
        if existing_item is None:
            raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found")

        update_query = items.update().where(items.c.id == item_id).values(name=item.name, description=item.description)
        await db.execute(update_query)
        return {"id": item_id, **item.dict()}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
    finally:
        await db.disconnect()
