#!/bin/bash

echo "> 배포 시작" >> /home/ec2-user/deploy.log

cd /home/ec2-user/app
sudo docker-compose pull
sudo docker-compose up --build -d

# 이전 버전의 이미지 정리
echo "> 이전 버전의 Docker 이미지 정리" >> /home/ec2-user/deploy.log
sudo docker image prune -f

echo "> 배포 완료" >> /home/ec2-user/deploy.log
