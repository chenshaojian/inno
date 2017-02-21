sudo kill -9 `sudo lsof -t -i:8008`
python manage.py runserver 0.0.0.0:8008
