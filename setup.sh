set -a
source ./.env
set +a

sed -i "s|\$OPENAI_API_KEY|$OPENAI_API_KEY|g" "logService.py"
sed -i "s|\$JUPYTERHUB_URL|$JUPYTERHUB_URL|g" "logService.py"
sed -i "s|\$MONGO_INITDB_ROOT_USERNAME|$MONGO_INITDB_ROOT_USERNAME|g" "logService.py"
sed -i "s|\$MONGO_INITDB_ROOT_PASSWORD|$MONGO_INITDB_ROOT_PASSWORD|g" "logService.py"

sed -i "s|\$MONGO_INITDB_ROOT_USERNAME|$MONGO_INITDB_ROOT_USERNAME|g" "docker-compose.yml"
sed -i "s|\$MONGO_INITDB_ROOT_PASSWORD|$MONGO_INITDB_ROOT_PASSWORD|g" "docker-compose.yml"

sed -i "s|\$COURSE_NAME|$COURSE_NAME|g" "jupyterhub_config.py"
sed -i "s|\$STUDENT_IMAGE_NAME|$STUDENT_IMAGE_NAME|g" "jupyterhub_config.py"
sed -i "s|\$ADMIN_USERNAME|$ADMIN_USERNAME|g" "jupyterhub_config.py"


sed -i "s|\$JUPYTERHUB_URL|$JUPYTERHUB_URL|g" "./studentContainers/extensionManager/extension/src/index.ts"
sed -i "s|\$JUPYTERHUB_URL|$JUPYTERHUB_URL|g" "./studentContainers/noSupportExtension/extension/src/index.ts"
sed -i "s|\$JUPYTERHUB_URL|$JUPYTERHUB_URL|g" "./studentContainers/genericSupportExtension/extension/src/index.ts"
sed -i "s|\$JUPYTERHUB_URL|$JUPYTERHUB_URL|g" "./studentContainers/personalizedSupportExtension/extension/src/index.ts"
sed -i "s|\$JUPYTERHUB_URL|$JUPYTERHUB_URL|g" "./studentContainers/customPromptExtension/extension/src/index.ts"


docker build -t ${STUDENT_IMAGE_NAME}:latest --label "courseName=${COURSE_NAME}" ./studentContainers --no-cache

docker compose build --no-cache
docker compose up -d