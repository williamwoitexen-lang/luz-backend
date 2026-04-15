#!/bin/bash
# Script para rollback de deploy no Azure Container Apps

set -e

APP_NAME=${1:-"ca-peoplechatbot-dev-latam001"}
RESOURCE_GROUP=${2:-"rg-dev-latam001"}

echo "⚠️  ROLLBACK - Revertendo para versão anterior"
echo "App: $APP_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo ""

# Get the current revision
echo "📋 Listando revisões disponíveis..."
az containerapp revision list \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "[].{name:name, created:properties.createdTime, active:properties.active}" \
  --output table

echo ""
echo "🔄 Revertendo para versão anterior..."

# Get the previous revision (not the latest)
PREVIOUS_REVISION=$(az containerapp revision list \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "[1].name" \
  --output tsv)

if [ -z "$PREVIOUS_REVISION" ]; then
  echo "❌ Nenhuma revisão anterior encontrada!"
  exit 1
fi

echo "Ativando revisão anterior: $PREVIOUS_REVISION"

# Activate the previous revision (make it ready)
az containerapp revision activate \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --revision "$PREVIOUS_REVISION"

# Deactivate the current (broken) revision
CURRENT_REVISION=$(az containerapp revision list \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "[0].name" \
  --output tsv)

if [ ! -z "$CURRENT_REVISION" ] && [ "$CURRENT_REVISION" != "$PREVIOUS_REVISION" ]; then
  echo "Desativando revisão atual (broken): $CURRENT_REVISION"
  az containerapp revision deactivate \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --revision "$CURRENT_REVISION"
fi

echo ""
echo "✅ Rollback concluído!"
echo ""
echo "📊 Status das revisões:"
az containerapp revision list \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "[].{name:name, active:properties.active}" \
  --output table
