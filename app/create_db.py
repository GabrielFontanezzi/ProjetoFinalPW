import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base, engine
# Cria todas as tabelas definidas em 'Base'
Base.metadata.create_all(bind=engine)
