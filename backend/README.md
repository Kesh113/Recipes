### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone git@github.com:Kesh113/foodgram.git
```

```bash
cd backend
```

Cоздать и активировать виртуальное окружение:

```bash
py -3.9 -m venv env
```

* Если у вас Linux/macOS

```bash
source env/bin/activate
```

* Если у вас windows

```bash
source env/scripts/activate
```

```bash
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```bash
pip install -r requirements.txt
```

Выполнить миграции:

```bash
python3 manage.py migrate
```

Добавить обязательные переменные окружения:

Вместо значений переменных подставьте свои.

```bash
echo 'POSTGRES_DB=foodgram' >> .env
echo 'POSTGRES_USER=foodgram_user' >> .env
echo 'POSTGRES_PASSWORD=foodgram_password' >> .env
echo 'DB_HOST=db' >> .env
echo 'DB_PORT=5432' >> .env
echo 'SECRET_KEY=secret_key' >> .env
echo 'DEBUG=False' >> .env
echo 'ALLOWED_HOSTS=127.0.0.1,localhost' >> .env
echo 'SQLITE=False' >> .env
```

Запустить проект:

```bash
python3 manage.py runserver
```