#!/bin/bash

DEPLOY_LOG="/home/ec2-user/deploy.log"
# 배포 로그 파일 초기화
echo "" > $DEPLOY_LOG

echo "$(date '+%Y-%m-%d %H:%M:%S') > 배포 시작" >> $DEPLOY_LOG

# shellcheck disable=SC2164
cd /home/ec2-user/app

# .env 파일 생성 또는 초기화
echo "$(date '+%Y-%m-%d %H:%M:%S') > Initializing .env" >> $DEPLOY_LOG
echo "" > .env

# 환경 변수 가져오기 및 .env 파일에 기록
echo "$(date '+%Y-%m-%d %H:%M:%S') > Writing Environmental variables into .env file" >> $DEPLOY_LOG
echo "DB_HOST=$(aws ssm get-parameter --name "/DB_HOST" --query "Parameter.Value" --output text)" >> .env
echo "DB_PORT=$(aws ssm get-parameter --name "/DB_PORT" --query "Parameter.Value" --output text)" >> .env
echo "DB_NAME=$(aws ssm get-parameter --name "/DB_NAME" --query "Parameter.Value" --output text)" >> .env
echo "DB_PASSWORD=$(aws ssm get-parameter --name "/DB_PASSWORD" --query "Parameter.Value" --output text)" >> .env
echo "DB_USER=$(aws ssm get-parameter --name "/DB_USER" --query "Parameter.Value" --output text)" >> .env
echo "GOOGLE_CLIENT_ID=$(aws ssm get-parameter --name "/GOOGLE_CLIENT_ID" --query "Parameter.Value" --output text)" >> .env
echo "GOOGLE_CLIENT_SECRET=$(aws ssm get-parameter --name "/GOOGLE_CLIENT_SECRET" --query "Parameter.Value" --output text)" >> .env
echo "SECRET_KEY=$(aws ssm get-parameter --name "/SECRET_KEY" --query "Parameter.Value" --output text)" >> .env
echo "APP_ENV=$(aws ssm get-parameter --name "/APP_ENV" --query "Parameter.Value" --output text)" >> .env
echo "KAKAO_CLIENT_ID=$(aws ssm get-parameter --name "/KAKAO_CLIENT_ID" --query "Parameter.Value" --output text)" >> .env
echo "KAKAO_CLIENT_SECRET=$(aws ssm get-parameter --name "/KAKAO_CLIENT_SECRET" --query "Parameter.Value" --output text)" >> .env
echo "NAVER_CLIENT_ID=$(aws ssm get-parameter --name "/NAVER_CLIENT_ID" --query "Parameter.Value" --output text)" >> .env
echo "NAVER_CLIENT_SECRET=$(aws ssm get-parameter --name "/NAVER_CLIENT_SECRET" --query "Parameter.Value" --output text)" >> .env
echo "REDIRECT_URI=$(aws ssm get-parameter --name "/REDIRECT_URI" --query "Parameter.Value" --output text)" >> .env
echo "LOGIN_REDIRECT_URL=$(aws ssm get-parameter --name "/LOGIN_REDIRECT_URL" --query "Parameter.Value" --output text)" >> .env
echo "REDIS_HOST=$(aws ssm get-parameter --name "/REDIS_HOST" --query "Parameter.Value" --output text)" >> .env
echo "S3_ACCESS_KEY=$(aws ssm get-parameter --name "/S3_ACCESS_KEY" --query "Parameter.Value" --output text)" >> .env
echo "S3_SECRET_KEY=$(aws ssm get-parameter --name "/S3_SECRET_KEY" --query "Parameter.Value" --output text)" >> .env
echo "MONGO_URI=$(aws ssm get-parameter --name "/MONGO_URI" --query "Parameter.Value" --output text)" >> .env
echo "MONGODB_DATABASE=$(aws ssm get-parameter --name "/MONGODB_DATABASE" --query "Parameter.Value" --output text)" >> .env
# 몽고디비 변수 설정해야됨

aws s3 cp s3://blue-rally/metadata.txt metadata.txt
IMAGE_TAG=$(cat metadata.txt)

# Docker 이미지 다운로드 및 서비스 시작 로깅
echo "$(date '+%Y-%m-%d %H:%M:%S') > Pulling Docker image with tag: $IMAGE_TAG" >> $DEPLOY_LOG
sudo docker pull bluerally/bluerally-be:$IMAGE_TAG 2>&1 | tee -a $DEPLOY_LOG

# Docker 이미지 태그 업데이트
sudo sed -i "s/bluerally\/bluerally-be:latest/bluerally\/bluerally-be:$IMAGE_TAG/g" docker-compose.yml

echo "$(date '+%Y-%m-%d %H:%M:%S') > Starting Docker Compose services" >> $DEPLOY_LOG
sudo docker-compose down 2>&1 | tee -a $DEPLOY_LOG
sudo docker-compose up -d 2>&1 | tee -a $DEPLOY_LOG

# Docker Compose를 사용하여 Aerich 마이그레이션 실행
echo "$(date '+%Y-%m-%d %H:%M:%S') > Running Aerich database migrations" >> $DEPLOY_LOG
sudo docker-compose run --rm app aerich upgrade 2>&1 | tee -a $DEPLOY_LOG

# 오래된 Docker 이미지 정리
echo "$(date '+%Y-%m-%d %H:%M:%S') > Cleaning up old Docker images" >> $DEPLOY_LOG
sudo docker image prune -a -f 2>&1 | tee -a $DEPLOY_LOG

echo "$(date '+%Y-%m-%d %H:%M:%S') > 배포 완료" >> $DEPLOY_LOG
