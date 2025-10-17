# ToDoList_FastAPI
ToDoList with Python, FastAPI, SQLite, OAuth2, JWT and Docker for containerization.

Run:

>docker build -t to_do_list_api:latest .

>docker compose up -d –build

>docker ps

>docker logs -f to_do_list_api

Browser: http://127.0.0.1:8080/docs   # will see the Swagger UI

![test](browser.png)

Test:

# 1) Create new user (register):
>curl -X POST http://127.0.0.1:8080/users/ -H "Content-Type: application/json" -d
"{\"username\":\"John\",\"password\":\"parola123\",\"full_name\":\"John Tardy\"}"

# 2) Get token (OAuth2 Password Grant)
>curl -X POST http://127.0.0.1:8080/token -H "Content-Type: application/x-www-form-
urlencoded" -d "username=John&password=parola123"
# response: {"access_token":"eyJ...", "token_type":"bearer"}

# 3) Create a new task:
>curl -X POST http://127.0.0.1:8080/todolist -H "Authorization: Bearer
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJHZW8iLCJleHAiOjE3NjAzNjA5Mzd9.gfy
ANyGyzYGIkyaIT2tIE_hzbKxPCAie-bhF8wGVC7Y" -H "Content-Type: application/json" -d
"{\"task_name\":\"curatenie\",\"task_description\":\"spalat vase\",\"status\":\"pending\"}"

# 4) Listing tasks from current user:
>curl -X GET http://127.0.0.1:8080/taskuri_existente -H "Authorization: Bearer
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJHZW8iLCJleHAiOjE3NjAzNjA5Mzd9.gfy
ANyGyzYGIkyaIT2tIE_hzbKxPCAie-bhF8wGVC7Y"
