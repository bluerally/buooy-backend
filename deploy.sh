#!/bin/bash

echo "> 배포 시작" >> /home/ec2-user/deploy.log

cd /home/ec2-user/app

# Pulling the latest image based on tag
echo "> Pulling latest Docker images" >> /home/ec2-user/deploy.log
IMAGE_TAG=$(git describe --tags --abbrev=0)
sudo docker-compose pull app:$IMAGE_TAG

# Starting services
echo "> Starting Docker Compose services" >> /home/ec2-user/deploy.log
sudo docker-compose up -d

# Cleaning up old images
echo "> Cleaning up old Docker images" >> /home/ec2-user/deploy.log
sudo docker image prune -f

echo "> 배포 완료" >> /home/ec2-user/deploy.log
