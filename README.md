# Project Setup

## 1. Create a `.env` File

Create a `.env` file in your project root to store environment variables:

```env
# .env
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
DEBUG=True
```

## 2. Run with Docker Compose

Make sure you have a `docker-compose.yml` file configured. Then, start your services:

```sh
docker compose up --build
```

## 3. Run Tests with Pytest and Coverage

To run tests with coverage inside your Docker container:

```sh
docker compose exec <service_name> pytest --cov=.
```

Replace `<service_name>` with the name of your app service as defined in `docker-compose.yml`.
