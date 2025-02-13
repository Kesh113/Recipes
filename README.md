![badge_foodgram](https://github.com/kesh113/foodgram/actions/workflows/main.yml/badge.svg)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-3.2+-green.svg)](https://www.djangoproject.com/)

# Foodgram

## Описание проекта

**Foodgram** — это веб-приложение, созданное на Django, которое позволяет пользователям делиться своими любимыми кулинарными рецептами, находить вдохновение и создавать списки покупок. Это своего рода кулинарная социальная сеть, где вы можете подписываться на других пользователей, добавлять рецепты в избранное и многое другое.

### Основные функции:

*   **Публикация рецептов:** Пользователи могут создавать и публиковать собственные кулинарные рецепты с подробным описанием ингредиентов, шагов приготовления и фотографиями.
*   **Редактирование рецептов:** Пользователи могут изменять свои опубликованные рецепты.
*   **Избранное:** Пользователи могут добавлять рецепты других пользователей в список избранного для быстрого доступа.
*   **Список покупок:** Пользователи могут добавлять ингредиенты из рецептов в список покупок, который автоматически подсчитывает необходимое количество каждого ингредиента.
*   **Скачивание списка покупок:** Пользователи могут скачать список покупок в формате .txt для удобного использования в магазине.
*   **Подписки:** Пользователи могут подписываться на других пользователей и видеть рецепты своих подписок в отдельной ленте.
*   **Короткие ссылки:** Пользователи могут создавать короткие ссылки на отдельные рецепты для удобного обмена.
*   **Регистрация и аутентификация:** Пользователи могут создавать учетные записи, аутентифицироваться и безопасно управлять своими профилями.
*   **Смена пароля:** Пользователи могут изменять свой пароль для повышения безопасности аккаунта.
*   **Аватар пользователя:** Пользователи могут загружать и удалять аватары для персонализации своего профиля.

## Стек технологий

- **Язык программирования**: Python 3.9
- **Веб-фреймворк**: Django
- **REST API**: Django REST Framework
- **Аутентификация**: Djoser
- **База данных**: PostgreSQL
- **Обработка изображений**: Pillow
- **Тестирование**: flake8
- **Развертывание**: Gunicorn, Nginx, Docker
- **Конфигурация**: PyYAML

## Как развернуть проект

1. **Клонируйте репозиторий**:

```bash
git clone git@github.com:Kesh113/foodgram.git
cd foodgram
```

2. **Добавьте обязательные переменные окружения**

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

### В контейнерах Docker

3. **Установите Docker**

```bash
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin 
```

4. **Разверните контейнеры**

```bash
docker compose up -d
```

5. **Выполните миграции и передайте статику с бэкэнда**

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
```

6. **Загрузите фикстуры**

CSV:
```bash
docker compose exec backend python manage.py load_csv ingredients
docker compose exec backend python manage.py load_csv tags
```

**ЛИБО**

JSON:
```bash
docker compose exec backend python manage.py load_json foodgram/fixtures/ingredients.json foodgram.Ingredient
docker compose exec backend python manage.py load_json foodgram/fixtures/tags.json foodgram.Tag
```

7. **Cоздайте root пользователя**

```bash
docker compose exec backend python manage.py createsuperuser
```

8 **Пользуйтесь сервисом** 

[тык](http://localhost:8000)

### Локально

3. **Создайте и активируйте виртуальное окружение**

```bash
cd backend/
py -3.9 -m venv venv
source venv/Scripts/activate
```

4. **Установите зависимости**

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5. **Выполните миграции и импортируйте фикстуры**

```bash
python manage.py migrate
```

JSON:
```bash
python manage.py load_json foodgram/fixtures/ingredients.json foodgram.Ingredient
python manage.py load_json foodgram/fixtures/tags.json foodgram.Tag
```

**ЛИБО**

CSV:
```bash
python manage.py load_csv ingredients
python manage.py load_csv tags
```

6. **Создайте root пользователя и запустите бэкэнд сервер**

```bash
python manage.py createsuperuser
python manage.py runserver
```

7. **Изменить настройки в frontend/package.json**

"proxy": "http://web:8000/" -> "proxy": "http://localhost:8000/"

**Не забудьте поменять настройки обратно при передаче на продакшн**

8. **Запустите фронтэнд сервер**

```bash
cd ../frontend
npm run start
```

9 **Пользуйтесь сервисом** 

[Бэкэнд](http://localhost:8000)
[Фронтэнд](http://localhost:3000)


## Автор

Широкожухов Артем Андреевич

[Мой Foodgram](https://www.ya-kesh.ru/)

[GitHub](https://github.com/Kesh113)