## 🐳 Docker Cleanup Guide
Use these commands to reset your environment or reclaim disk space.
## 1. The "Fresh Start" (Recommended)
This removes all stopped containers, unused networks, and dangling images/volumes.

docker system prune --volumes -f

## 2. The "Nuclear Option" (Deep Clean)
Deletes everything—including all images, active containers, and persistent data volumes.

# Stop all running containers first
docker stop $(docker ps -aq)
# Remove all containers, images, and volumes
docker system prune -a --volumes -f

## 3. Docker Compose Reset
If using docker-compose.yml, this shuts down the stack and wipes the specific images and volumes associated with it.

docker compose down --rmi all --volumes --remove-orphans

## 4. Individual Cleanup

* Containers: docker rm -f $(docker ps -aq)
* Images: docker rmi -f $(docker images -q)
* Volumes: docker volume rm $(docker volume ls -q)
