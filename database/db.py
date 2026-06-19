from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(
    "sqlite:///inventory.db",
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def init_db():
    from database import models

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        product_columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(products)"))
        }

        product_migrations = {
            "supplier_name": "ALTER TABLE products ADD COLUMN supplier_name VARCHAR",
            "supplier_email": "ALTER TABLE products ADD COLUMN supplier_email VARCHAR",
            "supplier_phone": "ALTER TABLE products ADD COLUMN supplier_phone VARCHAR",
            "lead_time_days": "ALTER TABLE products ADD COLUMN lead_time_days INTEGER DEFAULT 0",
        }

        for column_name, sql in product_migrations.items():
            if column_name not in product_columns:
                conn.execute(text(sql))

        tables = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }

        if "purchase_orders" not in tables:
            Base.metadata.create_all(bind=engine)
        else:
            purchase_order_columns = {
                row[1]
                for row in conn.execute(text("PRAGMA table_info(purchase_orders)"))
            }

            purchase_order_migrations = {
                "supplier_name": "ALTER TABLE purchase_orders ADD COLUMN supplier_name VARCHAR",
                "supplier_email": "ALTER TABLE purchase_orders ADD COLUMN supplier_email VARCHAR",
                "supplier_phone": "ALTER TABLE purchase_orders ADD COLUMN supplier_phone VARCHAR",
                "lead_time_days": "ALTER TABLE purchase_orders ADD COLUMN lead_time_days INTEGER DEFAULT 0",
                "unit_price": "ALTER TABLE purchase_orders ADD COLUMN unit_price REAL DEFAULT 0",
            }

            for column_name, sql in purchase_order_migrations.items():
                if column_name not in purchase_order_columns:
                    conn.execute(text(sql))

        conn.commit()
