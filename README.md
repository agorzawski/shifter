# Shifter
A simple system for displaying and managing:
- members, roles, teams,
- campaigns, time slots and assigned shifts.

Using
- Django
- https://fullcalendar.io/docs

## Installation

Create a new virtual environment:

```sh
virtualenv ./venv/django_env
source ./venv/django_env/bin/activate
```

Install the requirements and iPython to have a nice shell:

```sh
pip install -r requirements.txt
pip install ipython
```

Setup the development environment variables:

```sh
export DJANGO_SECRET_KEY='8(m)79e5&@(8we&i$2o(dqg7th4!$3(iivzustzr*$jvwc5ij^'
export DJANGO_DEBUG=1
export DJANGO_LOCAL_DEV=1
```

*Note, this is not the production secret key ;-)*

Initialise the database:

```sh
python manage.py migrate
```

Start the development server:

```sh
python manage.py runserver
```

You should now be able to visit the website:
http://127.0.0.1:8000
