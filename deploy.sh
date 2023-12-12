#!/bin/bash

echo "$(date '+%Y-%m-%d %H:%M:%S') > 배포 시작" >> /home/ec2-user/deploy.log

cd /home/ec2-user/app

aws s3 cp s3://blue-rally/metadata.txt metadata.txt
IMAGE_TAG=$(cat metadata.txt)

echo "$(date '+%Y-%m-%d %H:%M:%S') > Pulling latest Docker image with tag: $IMAGE_TAG" >> /home/ec2-user/deploy.log
sudo docker pull bluerally/bluerally-be:$IMAGE_TAG

sudo sed -i "s/image: bluerally\/bluerally-be:.*/image: bluerally\/bluerally-be:$IMAGE_TAG/" docker-compose.yml
echo "$(date '+%Y-%m-%d %H:%M:%S') > Starting Docker Compose services" >> /home/ec2-user/deploy.log
sudo docker-compose down
sudo docker-compose up -d

echo "$(date '+%Y-%m-%d %H:%M:%S') > Cleaning up old Docker images" >> /home/ec2-user/deploy.log
sudo docker image prune -f

echo "$(date '+%Y-%m-%d %H:%M:%S') > 배포 완료" >> /home/ec2-user/deploy.log
