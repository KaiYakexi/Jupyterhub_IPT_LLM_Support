set -a
source ./.env
set +a

sed -i "s|\$OPENAI_API_KEY|$OPENAI_API_KEY|g" "logService.py"
sed -i "s|\$JUPYTERHUB_URL|$JUPYTERHUB_URL|g" "logService.py"
sed -i "s|\$MONGO_INITDB_ROOT_USERNAME|$MONGO_INITDB_ROOT_USERNAME|g" "logService.py"
sed -i "s|\$MONGO_INITDB_ROOT_PASSWORD|$MONGO_INITDB_ROOT_PASSWORD|g" "logService.py"

sed -i "s|\$MONGO_INITDB_ROOT_USERNAME|$MONGO_INITDB_ROOT_USERNAME|g" "docker-compose.yml"
sed -i "s|\$MONGO_INITDB_ROOT_PASSWORD|$MONGO_INITDB_ROOT_PASSWORD|g" "docker-compose.yml"

sed -i "s|\$MONGO_INITDB_ROOT_USERNAME|$MONGO_INITDB_ROOT_USERNAME|g" "docker-compose.prod.yml"
sed -i "s|\$MONGO_INITDB_ROOT_PASSWORD|$MONGO_INITDB_ROOT_PASSWORD|g" "docker-compose.prod.yml"

sed -i "s|\$ABSOLUTE_PATH_TO_COURSE_DIRECTORY|$ABSOLUTE_PATH_TO_COURSE_DIRECTORY|g" "jupyterhub_config.py"

sed -i "s|\$ABSOLUTE_PATH_TO_COURSE_DIRECTORY|$ABSOLUTE_PATH_TO_COURSE_DIRECTORY|g" "studentContainers/addToContainer.sh"

docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d