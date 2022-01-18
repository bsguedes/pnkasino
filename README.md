# pnkasino

A betting place for friends.

## Installation

Please check that you have Python 3.8 installed.

After cloning the repo and navigating to the project directory:

### Install flask and venv:

`sudo apt install python3-flask`

`sudo apt install python3.8-venv`

### Activate the environment and install the packages:

`python3 -m venv pnkasino`

`source pnkasino/bin/activate`

`python -m pip install -r requirements.txt`

### Install postgres:

`sudo apt-get install postgresql`

### Set project environment variables

`export SECRET_KEY=something`

`export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/postgres`

### Run the migrations:

`alembic upgrade head`

### Run the app:

`flask run --no-reload`
