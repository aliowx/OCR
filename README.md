# ACQUIRER FASTAPI PROJECT

## for develop the project you need:

- docker / docker compose **(first of all install)**
- postgres
- redis
- pgadmin

**_note: there is no need to install postgres and redis in your local system_**

## setup the project

### step1: create .env file

create .env file in root project and fill up like .env.example and copy that .env file in ./app

**_note: to create secret key use this command:_**

```
openssl rand -base64 64

```

### step2: docker login

you must be login:

```
docker login [url]

```

### step3: up the postgres and redis

in our project there is the **_docker-compose.dev.yml_**
use this file to up postgres and redis

```
docker compose -f docker-compose.dev.yml up -d

```

### step4: install dependency

if you do not have poetry package manager install that

in our root project directory go to app folder

for create virtual env and go to that and after that install dependency use below commands

```

poetry shell

poetry install

```

maybe you get some error for some library so you need in virtual env install them individualy

```
pip install [name_of_library]==[version]

```

### step5: run the app

after install dependency so next and last step is run the

```
uvicorn --reload --host 0.0.0.0 --port 8000 --log-level info "app.main:app"

```

## Migrate project

create migration file with:

```
alembic revision --autogenerate
```

apply migration with:

```commandline
alembic upgrade head
```


## Multiple Authentications Methods

to enable multiple authentication add ALLOWED_AUTH_METHODS to environment variables:

```ALLOWED_AUTH_METHODS=basic,jwt``` 


## Test websocket

in order to test websocket paste this line in api test-websocket

```commandline
ws://ip:port/api/v1/utils/echo-client/
```

and paste response in html file and open it