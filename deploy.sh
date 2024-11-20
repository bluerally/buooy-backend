#!/bin/bash

DEPLOY_LOG="/home/ec2-user/deploy.log"
# 배포 로그 파일 초기화
echo "" > $DEPLOY_LOG

echo "$(date '+%Y-%m-%d %H:%M:%S') > 배포 시작" >> $DEPLOY_LOG

# shellcheck disable=SC2164
cd /home/ec2-user/app

# AWS SSM에서 환경변수 가져오기
echo "$(date '+%Y-%m-%d %H:%M:%S') > 환경변수 수집" >> $DEPLOY_LOG

# AWS SSM에서 모든 환경변수 추출
ENVIRONMENT_VARS=(
  "DB_HOST" "DB_PORT" "DB_NAME" "DB_PASSWORD" "DB_USER"
  "GOOGLE_CLIENT_ID" "GOOGLE_CLIENT_SECRET"
  "SECRET_KEY" "APP_ENV"
  "KAKAO_CLIENT_ID" "KAKAO_CLIENT_SECRET"
  "NAVER_CLIENT_ID" "NAVER_CLIENT_SECRET"
  "REDIRECT_URI" "LOGIN_REDIRECT_URL"
  "REDIS_HOST"
  "S3_ACCESS_KEY" "S3_SECRET_KEY"
  "MONGO_URI" "MONGODB_DATABASE"
)

# Docker run 명령어에 사용할 환경변수 옵션 생성
ENV_OPTIONS=""
for var in "${ENVIRONMENT_VARS[@]}"; do
  value=$(aws ssm get-parameter --name "/$var" --query "Parameter.Value" --output text)
  ENV_OPTIONS+=" -e $var='$value'"
done

# S3에서 이미지 태그 가져오기
aws s3 cp s3://buooy/metadata.txt metadata.txt
IMAGE_TAG=$(cat metadata.txt)

echo "$(date '+%Y-%m-%d %H:%M:%S') > Docker 이미지 다운로드: $IMAGE_TAG" >> $DEPLOY_LOG
sudo docker pull bluerally/bluerally-be:$IMAGE_TAG 2>&1 | tee -a $DEPLOY_LOG

# 기존 컨테이너 중지 및 삭제
echo "$(date '+%Y-%m-%d %H:%M:%S') > 기존 컨테이너 정리" >> $DEPLOY_LOG
sudo docker stop buooy-be || true
sudo docker rm buooy-be || true

# 새 컨테이너 실행
echo "$(date '+%Y-%m-%d %H:%M:%S') > 새 컨테이너 실행" >> $DEPLOY_LOG
sudo docker run -d \
  --name buooy-be \
  -p 8080:8080 \
  -v /home/ec2-user/logs:/app/logs \
  $ENV_OPTIONS \
  bluerally/bluerally-be:$IMAGE_TAG 2>&1 | tee -a $DEPLOY_LOG

# Aerich 데이터베이스 마이그레이션 실행
echo "$(date '+%Y-%m-%d %H:%M:%S') > Running Aerich database migrations" >> $DEPLOY_LOG
sudo docker exec buooy-be aerich upgrade 2>&1 | tee -a $DEPLOY_LOG

# 오래된 Docker 이미지 정리
echo "$(date '+%Y-%m-%d %H:%M:%S') > 오래된 Docker 이미지 정리" >> $DEPLOY_LOG
sudo docker image prune -a -f 2>&1 | tee -a $DEPLOY_LOG

echo "$(date '+%Y-%m-%d %H:%M:%S') > 배포 완료" >> $DEPLOY_LOG
