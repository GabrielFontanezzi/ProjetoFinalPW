# main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from starlette.requests import Request
from datetime import timedelta
from app import models, schemas, crud, auth, database
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

models.Base.metadata.create_all(bind=database.engine)

class Token(BaseModel):
    access_token: str
    token_type: str

# Função para obter uma sessão de banco de dados
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função para criar um usuário
def create_user(db: Session, name: str, email: str, password: str):
    hashed_password = password  # Aqui você deve adicionar o código de hashing real
    db_user = models.User(username=name, email=email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Função para obter um usuário por email
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# Exemplo de uso
if __name__ == "__main__":
    # Cria a sessão de banco de dados
    with database.SessionLocal() as db:
        # Cria um novo usuário
        new_user = create_user(db, name="John Doe", email="johndoe@example.com", password="password123")
        print(f"Usuário criado: {new_user.username}, {new_user.email}")

        # Consulta um usuário por email
        user = get_user_by_email(db, email="johndoe@example.com")
        print(f"Usuário consultado: {user.username}, {user.email}")

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/books", response_class=HTMLResponse)
async def read_books(request: Request, db: Session = Depends(database.SessionLocal)):
    books = crud.get_books(db)
    return templates.TemplateResponse("books.html", {"request": request, "books": books})

@app.post("/books/", response_model=schemas.Book)
async def create_book(book: schemas.BookCreate, db: Session = Depends(database.SessionLocal), current_user: schemas.User = Depends(auth.get_current_user)):
    return crud.create_book(db=db, book=book)

@app.get("/authors", response_class=HTMLResponse)
async def read_authors(request: Request, db: Session = Depends(database.SessionLocal)):
    authors = crud.get_authors(db)
    return templates.TemplateResponse("authors.html", {"request": request, "authors": authors})

@app.post("/authors/", response_model=schemas.Author)
async def create_author(author: schemas.AuthorCreate, db: Session = Depends(database.SessionLocal), current_user: schemas.User = Depends(auth.get_current_user)):
    return crud.create_author(db=db, author=author)

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
