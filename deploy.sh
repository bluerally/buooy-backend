#!/bin/bash

echo "$(date '+%Y-%m-%d %H:%M:%S') > 배포 시작" >> /home/ec2-user/deploy.log

cd /home/ec2-user/app

# 환경 변수 가져오기
DB_HOST=$(aws ssm get-parameter --name "/DB_HOST" --query "Parameter.Value" --output text)
DB_PORT=$(aws ssm get-parameter --name "/DB_PORT" --query "Parameter.Value" --output text)
DB_NAME=$(aws ssm get-parameter --name "/DB_NAME" --query "Parameter.Value" --output text)
DB_PASSWORD=$(aws ssm get-parameter --name "/DB_PASSWORD" --query "Parameter.Value" --output text)
DB_USER=$(aws ssm get-parameter --name "/DB_USER" --query "Parameter.Value" --output text)
GOOGLE_CLIENT_ID=$(aws ssm get-parameter --name "/GOOGLE_CLIENT_ID" --query "Parameter.Value" --output text)
GOOGLE_CLIENT_SECRET=$(aws ssm get-parameter --name "/GOOGLE_CLIENT_SECRET" --query "Parameter.Value" --output text)
SECRET_KEY=$(aws ssm get-parameter --name "/SECRET_KEY" --query "Parameter.Value" --output text)
APP_ENV=$(aws ssm get-parameter --name "/APP_ENV" --query "Parameter.Value" --output text)

# 환경변수를 Docker Compose 환경에 전달
export DB_HOST
export DB_PORT
export DB_NAME
export DB_PASSWORD
export DB_USER
export GOOGLE_CLIENT_ID
export GOOGLE_CLIENT_SECRET
export SECRET_KEY
export APP_ENV


aws s3 cp s3://blue-rally/metadata.txt metadata.txt
IMAGE_TAG=$(cat metadata.txt)

echo "$(date '+%Y-%m-%d %H:%M:%S') > Pulling latest Docker image with tag: $IMAGE_TAG" >> /home/ec2-user/deploy.log
sudo docker pull bluerally/bluerally-be:$IMAGE_TAG

sudo sed -i "s/image: bluerally\/bluerally-be:.*/image: bluerally\/bluerally-be:$IMAGE_TAG/" docker-compose.yml
echo "$(date '+%Y-%m-%d %H:%M:%S') > Starting Docker Compose services" >> /home/ec2-user/deploy.log
sudo docker-compose down

# Aerich 마이그레이션 실행
echo "$(date '+%Y-%m-%d %H:%M:%S') > Running Aerich database migrations" >> /home/ec2-user/deploy.log
sudo docker-compose run --rm app aerich upgrade

sudo docker-compose up -d

echo "$(date '+%Y-%m-%d %H:%M:%S') > Cleaning up old Docker images" >> /home/ec2-user/deploy.log
sudo docker image prune -a -f

echo "$(date '+%Y-%m-%d %H:%M:%S') > 배포 완료" >> /home/ec2-user/deploy.log
