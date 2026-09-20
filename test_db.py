from sqlalchemy import text

from app.database.connection import engine


try:
    with engine.connect() as connection:
        resultado = connection.execute(text("SELECT 1"))
        print("✅ Conexión exitosa con PostgreSQL")
        print("Resultado:", resultado.scalar())

except Exception as error:
    print("❌ Error de conexión")
    print(error)