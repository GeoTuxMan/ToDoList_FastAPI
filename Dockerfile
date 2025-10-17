# foloseste o imagine Python mica
FROM python:3.11-slim

# variabile de mediu pentru a nu produce bytecode si pentru pip
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# set working dir
WORKDIR /app

# instaleaza dependintele de sistem necesare pentru bcrypt/cryptography
RUN apt-get update && apt-get install -y build-essential libffi-dev libssl-dev gcc && rm -rf /var/lib/apt/lists/*

# copiaza fisierele requirements si instaleaza dependente
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copiaza codul aplicatiei
COPY . .

# expune portul pe care ruleaza uvicorn
EXPOSE 8080

# comanda default (rulează uvicorn)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
