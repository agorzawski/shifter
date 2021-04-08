# Shifter
A simple system for displaying (Web server) and managing/scheduling:
- members, roles, teams,
- campaigns, time slots, 
- assigned shifts.

Each shift that is saved in the system consists of mandatory (yellow) and optional (white) fields as shown in the Figure:
![](doc/Shifter_shift.png)
If ShiftRole is not assigned, a member-assigned role is displayed instead in the main overview.

## Import from the CSV file

If one provides a csv file (example below) 
that has start date in the file name, ie. ```some_name_ASOF__YYYY-MM-DD.csv ```
all shifts will be imported automatically.

```buildoutcfg
# name, day1, day2, day3, day4, day5, day6, day7 ....
name1, NWH, NWH, , , , , ,
name2, , , NWH, NWH,
```

> **Shift roles assignment:**
> - there may be a default shift-role assignment per import,
> - if the default is not assigned, the member roles will be used,
> - if the default should not be used ```@@``` tag should be used, e.g. ```AM:@@```, it will make use of member assigned role,
> - if different shift role should be used, mark it explicitly ```AM:TS2S```.
> 
>**Note**:
> - spaces between the comas are removed
> - if the shift is not found, the import default one is assigned.

>**IMPORTANT**:
>names and shift-day-slots need to be defined in the system.  
> In case name/slot is not found, given name-day-slot is skipped!

Advanced import
```buildoutcfg
# name, day1, day2, day3, day4, day5, day6, day7 ....
name1, NWH:@@, AM:OC, NMH:@@, NMH:OC, 
name2, NWH:@@, PM:OC, NMH:OC, NMH:@@, 
```

#### Available slots and roles
The initial import (see the later part of the installation part) provides the following shift slots:
```buildoutcfg
AM - morning
PM - afternoon
NWH - normal working hours
```

Shift roles:
```buildoutcfg
TS2S - TS2 Support
OC - On Call
OCC - On Call Cryo
OCE - On Call Electrical
OCI - On Call Infrastructure
OCPSS - On Call PSS
```

Member roles:
```buildoutcfg
SL - Shift Leader
OP - Operator
SE - System Expert
LM - Line Manager
```

# Installation

Requirements:
- Django (>3.x)
- https://fullcalendar.io/docs

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
And import the basic setup ()
```sh
python manage.py shell << 0001_create_basics.py
```

Start the development server:

```sh
python manage.py runserver
```

You should now be able to visit the website:
http://127.0.0.1:8000
