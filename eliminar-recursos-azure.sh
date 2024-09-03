#!/bin/bash

# Nombre del grupo de recursos
resource_group="TestLlamaIndexPython"

# Verificar si se ha proporcionado el nombre del grupo de recursos
if [ -z "$resource_group" ]; then
  echo "Error: Debes proporcionar el nombre del grupo de recursos."
  exit 1
fi

# Iniciar sesión en Azure (si no estás ya autenticado)
echo "Iniciando sesión en Azure..."
az login --only-show-errors
if [ $? -ne 0 ]; then
  echo "Error: Fallo al iniciar sesión en Azure."
  exit 1
fi

# Obtener la lista de IDs de recursos en el grupo de recursos
echo "Obteniendo lista de recursos en el grupo: $resource_group..."
resource_ids=$(az resource list --resource-group $resource_group --query "[].id" --output tsv)

# Verificar si se obtuvieron recursos
if [ -z "$resource_ids" ]; then
  echo "No se encontraron recursos en el grupo de recursos: $resource_group."
  exit 0
fi

# Iterar sobre cada ID de recurso y eliminarlo
echo "Eliminando recursos en el grupo de recursos: $resource_group..."
for resource_id in $resource_ids; do
  echo "Eliminando recurso: $resource_id"
  az resource delete --ids $resource_id --only-show-errors
  if [ $? -ne 0 ]; then
    echo "Error al eliminar el recurso: $resource_id"
  fi
done

echo "Proceso completado."
