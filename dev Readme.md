1. Swap $ADD_ABSOLUTE_PATH in jupyterhub_config.py with the absolute path to the course file directory.
2. Swap $ADD_API_KEY in logService.py with your openai api key.
3. Run: docker build -t courseone:latest --label "courseName=courseone" ./studentContainers --no-cache
4. Run docker compose build --no-cache
5. Run docker compose up
6. Open http://localhost:8533/jupyterhub/
7. Register an account using myadmin as the username
8. Go to the admin dashboard: http://localhost:8533/jupyterhub/hub/admin
9. Manage Groups -> Create "courseone" group -> add myadmin to courseone group
10. Start JupyterLab server
11. To use generic, custom or personalized or nosupport condition, check the example file in your jupyter environment.