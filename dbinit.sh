#!bin/bassh
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py addalgolist
python3 manage.py loaddata razupai3.json
