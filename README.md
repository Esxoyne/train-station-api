# Train Station API
API service for a train management system

Built using `Django REST Framework`

## Features

- JWT and simple token authentication

- Registration using e-mail

- Custom permission set

- Documentation using DRF Spectacular

- Ability to create, retrieve, update and delete railway stations, routes, trains and journeys

- Custom endpoint for uploading images to stations and trains

- Ability to order tickets for train journeys

## DB diagram

![ER diagram](db_diagram.png)

## Getting started

### Prerequisites

> Python 3 is required

### Installation

```shell
# clone the repo
git clone https://github.com/Esxoyne/train-station-api.git
cd train-station-api

# create and activate a virtual environment
python -m venv venv
source venv/bin/activate            # on Linux/macOS
venv\Scripts\Activate               # on Windows

# install dependencies
pip install -r requirements.txt

# start the server on localhost
python manage.py runserver
```

The application is running at `http://127.0.0.1:8000/`
