from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Numeric, Boolean, Date, TIMESTAMP, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

DATABASE_URL = "postgresql://cinna:1104@localhost:5432/glassdb"

engine = create_engine(DATABASE_URL, echo=True)  # Добавляем echo=True
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
metadata = MetaData()

# ORM модели
class Customer(Base):
    __tablename__ = 'customers'
    customer_id = Column(Integer, primary_key=True)
    customer_name = Column(String)
    address = Column(String)
    phone_number = Column(String)

class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    order_date = Column(Date)
    due_date = Column(Date)
    total_amount = Column(Numeric)

class GlassType(Base):
    __tablename__ = 'glass_type'
    type_id = Column(Integer, primary_key=True)
    type_name = Column(String)
    type_weight = Column(Numeric)
    type_height = Column(Numeric)
    is_mirror = Column(Boolean)
    price_per_sqm = Column(Numeric)

class Detail(Base):
    __tablename__ = 'detail'
    detail_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.order_id'))
    glass_type_id = Column(Integer, ForeignKey('glass_type.type_id'))
    width = Column(Numeric)
    height = Column(Numeric)
    is_completed = Column(Boolean, default=False)

class GlassRemnant(Base):
    __tablename__ = 'glass_remnants'
    remnant_id = Column(Integer, primary_key=True)
    glass_type_id = Column(Integer, ForeignKey('glass_type.type_id'))
    width = Column(Numeric)
    height = Column(Numeric)
    created_at = Column(TIMESTAMP)

# Core таблицы (для обратной совместимости)
customers = Table('customers', metadata, autoload_with=engine)
orders = Table('orders', metadata, autoload_with=engine)
detail = Table('detail', metadata, autoload_with=engine)
glass_type = Table('glass_type', metadata, autoload_with=engine)
glass_remnants = Table('glass_remnants', metadata, autoload_with=engine)

# Функция для получения сессии БД
def get_db():
    """
    Генератор сессий БД для использования в FastAPI Depends
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Создаём все таблицы (если их ещё нет)
def create_tables():
    Base.metadata.create_all(bind=engine)