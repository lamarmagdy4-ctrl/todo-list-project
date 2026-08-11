import sqlite3
from fastapi import FastAPI, Request, Form 
from fastapi.templating import Jinja2Templates
from werkzeug.security import generate_password_hash, check_password_hash
from fastapi.responses import RedirectResponse 
from fastapi.staticfiles import StaticFiles 
from starlette.middleware.sessions import SessionMiddleware 

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="simple-secret-key")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def create_database():
    connection = sqlite3.connect("todo.db")

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

create_database()


def create_user():
    connection = sqlite3.connect("todo.db")

    hashed_password = generate_password_hash("1234")

    connection.execute(
        "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
        ("test", hashed_password)
    )

    connection.commit()
    connection.close()

create_user()


@app.get("/")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@app.post("/")
def login_user(
    request: Request,
    username: str = Form (...),
    password: str = Form (...)
):

    connection = sqlite3.connect("todo.db")
    connection.row_factory = sqlite3.Row 

    user = connection.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    connection.close()

    if user and check_password_hash(user["password"], password):
        request.session["user"] = username
        return RedirectResponse(url="/home", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": "Invalid username or password"}
    )


@app.get("/home")
def tasks_page(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/", status_code=303)

    connection = sqlite3.connect("todo.db")
    connection.row_factory =sqlite3.Row

    tasks = connection.execute(
        "SELECT * FROM tasks"
    ).fetchall()

    connection.close()

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"tasks": tasks}
    )


@app.post("/home")
def add_task(title: str = Form(...)):
    connection = sqlite3.connect("todo.db")
    connection.execute(
        "INSERT INTO tasks (title) VALUES (?)",
        (title,)
    )

    connection.commit()
    connection.close()

    return RedirectResponse(url="/home", status_code=303)


@app.get("/delete/{task_id}")
def delete_task(task_id: int):
    connection = sqlite3.connect("todo.db")

    connection.execute(
        "DELETE FROM tasks WHERE id= ?",
        (task_id,)
    )

    connection.commit()
    connection.close()

    return RedirectResponse(url="/home", status_code=303)


@app.get("/profile")
def profile_page_(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="profile.html"
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
