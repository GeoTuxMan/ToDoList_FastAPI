from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt

# === Config database SQLite ===
DATABASE_URL = "sqlite:///./todolist.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# === Secret & settings for JWT ===
SECRET_KEY = "schimba_acest_secret"  # change before production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour (changes by needed)

# === Models SQLAlchemy ===
class Todolist(Base):
    __tablename__ = "todolist"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String, nullable=False)
    task_description = Column(String, nullable=False)
    status = Column(String, nullable=False)
    owner_username = Column(String, nullable=False, index=True)  # link with user

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)

# Create tables if not exist
Base.metadata.create_all(bind=engine)

# === Pydantic schemas ===
class TodoRequest(BaseModel):
    task_name: str
    task_description: str
    status: str

class TodoResponse(BaseModel):
    id: int
    task_name: str
    task_description: str
    status: str
    owner_username: str

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# === Password hashing ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# === OAuth2 scheme ===
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# === Util pentru DB ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Functions for auth ===
def get_user(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# === Dependency for user curent ===
from fastapi import Security

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nu s-a putut valida token-ul.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# optional: check activ
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # here can check flags (is_active etc.)
    return current_user

# === FastAPI app ===
app = FastAPI(title="TodoList with OAuth2 + JWT")

# === Endpoint pentru creare user (inregistrare) ===
@app.post("/users/", status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username deja folosit.")
    hashed = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed, full_name=user.full_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"username": new_user.username, "id": new_user.id}

# === Endpoint token (OAuth2 Password) ===
@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username sau parola incorecte",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# === Endpoint POST for add task (protected) ===
@app.post("/todolist", response_model=dict)
def create_task(request: TodoRequest, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    new_todolist = Todolist(
        task_name=request.task_name,
        task_description=request.task_description,
        status=request.status,
        owner_username=current_user.username
    )
    db.add(new_todolist)
    db.commit()
    db.refresh(new_todolist)
    return {"message": "Task saved succesfully", "id": new_todolist.id}

# === Endpoint GET for show existing tasks in database (only from current user) ===
@app.get("/taskuri_existente", response_model=List[TodoResponse])
def get_tasks(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    taskuri = db.query(Todolist).filter(Todolist.owner_username == current_user.username).all()
    return [
        TodoResponse(
            id=p.id,
            task_name=p.task_name,
            task_description=p.task_description,
            status=p.status,
            owner_username=p.owner_username
        )
        for p in taskuri
    ]


