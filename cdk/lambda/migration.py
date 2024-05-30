# from pathlib import Path
# import os

# from alembic import command
# from alembic.config import Config
# import logging
# import subprocess


# POSTGRES_USER = os.environ.get("POSTGRES_USER")
# POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
# POSTGRES_SERVER = os.environ.get("POSTGRES_SERVER")
# POSTGRES_PORT = os.environ.get("POSTGRES_PORT")
# POSTGRES_DB = os.environ.get("POSTGRES_DB")


# def run_migrations():
#     """Run database migrations using Alembic."""
#     # Run the Alembic upgrade command
#     result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)

#     if result.returncode != 0:
#         logging.error("Error running alembic upgrade head: %s", result.stderr)
#         raise RuntimeError(result.stderr)
#     else:
#         logging.info("Alembic upgrade head ran successfully: %s", result.stdout)


# def handler(event, context):
#     """Lambda function handler to run database migrations."""
#     try:
#         run_migrations()
#         return {"statusCode": 200, "body": "Database migrations completed successfully."}
#     except Exception as e:
#         return {"statusCode": 500, "body": f"Error running database migrations: {str(e)}"}


import json
import os
from pathlib import Path

from alembic import command
from alembic.config import Config

POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_SERVER = os.environ.get("POSTGRES_SERVER")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT")
POSTGRES_DB = os.environ.get("POSTGRES_DB")


def handler(event, context):
    alembic_ini_path = Path(__file__).parent / "alembic.ini"

    if not alembic_ini_path.is_file():
        raise FileNotFoundError(f"alembic.ini file not found at {alembic_ini_path}")

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option(
        "sqlalchemy.url",
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}",
    )

    command.upgrade(alembic_cfg, "head")

    return {"statusCode": 200, "body": json.dumps("Migrations successfully executed!")}
