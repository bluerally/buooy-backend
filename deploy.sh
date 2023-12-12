#!/bin/bash

echo "> 배포 시작" >> /home/ec2-user/deploy.log

cd /home/ec2-user/app

echo "> Pulling latest Docker image" >> /home/ec2-user/deploy.log
sudo docker pull bluerally/bluerally-be:latest

echo "> Starting Docker Compose services" >> /home/ec2-user/deploy.log
sudo docker-compose up -d

echo "> Cleaning up old Docker images" >> /home/ec2-user/deploy.log
sudo docker image prune -f

echo "> 배포 완료" >> /home/ec2-user/deploy.log
