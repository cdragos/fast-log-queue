# FastAPI API Endpoint with PostgreSQL and SQS Integration

This project consists of two services: an API and a worker. The API is built using FastAPI and allows writing log entries to a PostgreSQL database. The worker service integrates with Amazon SQS to offload the endpoint processing to a queue. The project utilizes AWS CDK (Cloud Development Kit) to deploy the necessary infrastructure, including Lambda functions, the database, and SQS.

Alembic is used for database migrations, ensuring a smooth and manageable database schema evolution.

## Table of Contents

1. [Requirements](#requirements)
2. [Setup](#setup)
3. [Running the Project](#running-the-project)
4. [Testing](#testing)
5. [Deployment](#deployment)
6. [Make Commands](#make-commands)
7. [Project Structure](#project-structure)
8. [Testing the Live API](#testing-the-live-api)

## Requirements

To run this project, you need the following:

- Python 3.11
- Node.js 20
- Docker
- Virtualenv
- AWS CLI

For Docker, it is recommended to install Orb Stack from [here](https://orbstack.dev/download) or by running `brew install orbstack`.

For the rest of the requirements, it is recommended to use Nix. You can download Nix from [here](https://nixos.org/download/) and then run the following command to set up the environment:

```bash
nix-shell -p python311 python311Packages.pip nodejs_20 zsh --run zsh
```

## Setup

### Installation

1. Clone the repository:

```bash
git clone git@github.com:cdragos/fast-log-queue.git
cd fast-log-queue
```

2. Set up the development environment:
```bash
make setup_dev
```

### Running the Project

1. Start the FastAPI development server:
```bash
fastapi dev api/main.py
```

2. Run the project using Docker Compose:
```bash
docker compose up
```

### Testing

To run the tests, use the following command:

```bash
make tests
```

### Deployment

1. Configure AWS CLI:
```bash
npm i aws-cli
npm i aws-cdk
aws configure
```

2. For the first-time deployment, run:
```bash
make bootstrap
```

3. Deploy the CDK stack:
```bash
make deploy
```

### Make Commands

The project includes several Make commands to simplify common tasks:

```bash
`make setup_dev`: Set up the development environment.
`make migrations`: Create a new Alembic migration.
`make upgrade`: Upgrade the database to the latest revision.
`make bootstrap`: Bootstrap the CDK stack.
`make deploy`: Deploy the CDK stack.
`make destroy`: Destroy the CDK stack.
`make test`: Run the unit tests.
```

## Project Structure

```bash
.
├── api/                    # FastAPI API application code
├── worker/                 # Worker service code
├── cdk/                    # AWS CDK stack definition
├── alembic_migrations/     # Alembic migration scripts
├── shared/                 # Shared configuration and models
├── tests/                  # Test files for API and worker
```

## Testing the Live API

To test the live API endpoint, you can use the following curl command:

```bash
curl -X POST "https://xw8f3zdndl.execute-api.us-east-1.amazonaws.com/logs" \
-H "Content-Type: application/json" \
-d '{
"message": "This is a test log entry",
"level": "INFO"
}'
```


To check the logs from the database, you can use the following curl command:
```
curl https://xw8f3zdndl.execute-api.us-east-1.amazonaws.com/logs
```
