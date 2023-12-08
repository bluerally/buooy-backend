# Bluerally Backend

## OutLine
Dive Match is a platform for free diving and scuba diving enthusiasts to find buddies. This service helps divers find partners for a safe and enjoyable diving experience.

## Functions
- Diver profile management(Sign-up, Authentication, Authorization)
- Find buddy and match

## Skills
- FastAPI(0.104.1)
- Uvicorn(0.24.0)
- Tortoise-ORM(0.20.0)
- Aerich(0.7.2)

## Installation

### Prerequisite
- Python version 3.12

### Install Procedure
   ```bash
   git clone https://github.com/audwls624/dive-match.git
   cd dive-match
   poetry install
   ```

### Environmental Variables
   - API_ENV: Application Environment (local, test, prod)
   - DB_HOST: Database Host
   - DB_PORT: Database Port
   - DB_USER: Database User
   - DB_PASSWORD: Database Password
   - DB_NAME: Database Name

### How to Run
   ```bash
   uvicorn main:app --reload
   ```

### Database Migration
   - Initialization
   ```bash
   aerich init -t common.config.DB_CONFIG
   ```
   - Generate Migration
   ```bash
   aerich migrate
   ```
   - Apply Migration
   ```bash
   aerich upgrade
   ```
