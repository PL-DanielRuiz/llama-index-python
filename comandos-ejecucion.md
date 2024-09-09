## Proyecto

> https://github.com/Azure-Samples/llama-index-python


## Azure

>  azd auth login


## Docker

> docker-compose up

Después iniciar modo debugger con `ctrl+shift+d` y tecla `F5`. Acceder a `http://localhost:8000/docs`.


- Espacio ocupado por imágenes, contenedores y volúmenes:
> docker system df

- Eliminar imagenes y contenedores
> docker image prune -a
> docker container prune

- Docker utiliza cache para acelerar el proceso de construcción de imágenes. Puedes limpiar este cache con el siguiente comando:
> docker builder prune -a


## APP

```bash
# backend/
python main.py
```

```bash
# frontend/
npm run dev
```


```bash
curl --location 'localhost:8000/api/chat/request' \
--header 'Content-Type: application/json' \
--data '{ "messages": [{ "role": "user", "content": "Hello" }] }'
```