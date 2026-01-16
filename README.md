# Project Setup

## 1) Create a .env file

Copy .env.example to .env:

Windows (PowerShell):
```powershell
Copy-Item .env.example .env
```

Windows (CMD):
```bat
copy .env.example .env
```

macOS/Linux:
```sh
cp .env.example .env
```

Open .env, fill in environment-specific values, and ensure .env is listed in .gitignore.


## 2) Google OAuth 2.0

- In Google Cloud Console:
    1) Create or choose a project.
    2) Configure the OAuth consent screen (add test users if External).
    3) Create Credentials → OAuth client ID → Web application.
    4) Add an Authorized redirect URI, e.g.:
         - http://localhost:5000/login/google/authorized

- Create the secret file from the template:
    - Copy client_secret.template.json to client_secret.json
        - Windows (PowerShell):
            ```powershell
            Copy-Item client_secret.template.json client_secret.json
            ```
        - Windows (CMD):
            ```bat
            copy client_secret.template.json client_secret.json
            ```
        - macOS/Linux:
            ```sh
            cp client_secret.template.json client_secret.json
            ```
    - Fill in client_id, project_id, and client_secret.

- Add to .env (if not already set):
    ```
    GOOGLE_CLIENT_ID=your-client-id
    GOOGLE_CLIENT_SECRET=your-client-secret
    ```

Security: never commit .env or client_secret.json; rotate credentials if leaked.


## 3) Start with Docker Compose

Ensure docker-compose.yml is configured, then start services:

```sh
docker compose up --build
```

Add -d to run detached. To stop services:

```sh
docker compose down
```


## 4) Run tests with pytest

On host:
```sh
pytest -q
```

In a Docker container:
```sh
docker compose exec SERVICE_NAME pytest -q
```

Replace SERVICE_NAME with your app service name from docker-compose.yml.
