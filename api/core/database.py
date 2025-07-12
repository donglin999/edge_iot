import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import logging

# SQLite Database for system state
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/iot.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# InfluxDB client for time series data
influxdb_client = None

async def init_db():
    """Initialize database connections"""
    global influxdb_client
    
    # Create SQLite tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize InfluxDB client
    try:
        influxdb_url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        influxdb_token = os.getenv("INFLUXDB_TOKEN")
        influxdb_org = os.getenv("INFLUXDB_ORG", "iot_org")
        
        if influxdb_token:
            influxdb_client = InfluxDBClient(
                url=influxdb_url,
                token=influxdb_token,
                org=influxdb_org
            )
            logging.info("InfluxDB client initialized successfully")
        else:
            logging.warning("InfluxDB token not provided, using mock client")
            
    except Exception as e:
        logging.error(f"Failed to initialize InfluxDB client: {e}")

def get_db():
    """Get SQLite database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_influxdb():
    """Get InfluxDB client"""
    return influxdb_client

def get_write_api():
    """Get InfluxDB write API"""
    if influxdb_client:
        return influxdb_client.write_api(write_options=SYNCHRONOUS)
    return None

def get_query_api():
    """Get InfluxDB query API"""
    if influxdb_client:
        return influxdb_client.query_api()
    return None