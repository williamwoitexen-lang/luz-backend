#!/bin/bash

# Azure Container Apps deployment script
# Usage: ./deploy-azure.sh <resource-group> <app-name> <image-uri>

set -e

RESOURCE_GROUP=${1:-"embeddings-rg"}
APP_NAME=${2:-"embeddings-api"}
IMAGE_URI=${3:-"myregistry.azurecr.io/embeddings:latest"}
LOCATION=${4:-"eastus"}

# Auto-scaling disabled until code is refactored (has in-memory state in temp_storage.py and stress_test.py)
# See: TODO_MULTI_INSTANCE_REFACTOR.md
MIN_REPLICAS=${MIN_REPLICAS:-1}           # Apenas 1 instância (sem auto-scale)
MAX_REPLICAS=${MAX_REPLICAS:-1}           # ⚠️ NÃO ESCALAR - código não é thread-safe entre instâncias
CPU_REQUEST=${CPU_REQUEST:-2}             # 2 CPUs
MEMORY_REQUEST=${MEMORY_REQUEST:-4}       # 4Gi

echo "🚀 Deploying Embeddings Service to Azure Container Apps"
echo "Resource Group: $RESOURCE_GROUP"
echo "App Name: $APP_NAME"
echo "Image URI: $IMAGE_URI"
echo "Location: $LOCATION"
echo "⚠️  Single instance only (NO AUTO-SCALING)"
echo "Resources: ${CPU_REQUEST} CPU, ${MEMORY_REQUEST}Gi RAM"

# Create resource group if it doesn't exist
echo "📦 Creating resource group..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none

# Create Container App Environment if it doesn't exist
ENVIRONMENT_NAME="${APP_NAME}-env"
echo "🌍 Creating Container App Environment..."
az containerapp env create \
  --name "$ENVIRONMENT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none 2>/dev/null || echo "Environment already exists"

# Deploy the container app with auto-scaling
echo "🐳 Deploying Container App..."
az containerapp create \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENVIRONMENT_NAME" \
  --image "$IMAGE_URI" \
  --target-port 8000 \
  --ingress external \
  --cpu "$CPU_REQUEST" \
  --memory "${MEMORY_REQUEST}Gi" \
  --min-replicas "$MIN_REPLICAS" \
  --max-replicas "$MAX_REPLICAS" \
  --query properties.configuration.ingress.fqdn \
  --env-vars \
    APP_ENV=PROD \
    STORAGE_TYPE=azure \
    AZURE_STORAGE_ACCOUNT_NAME="$AZURE_STORAGE_ACCOUNT_NAME" \
    AZURE_STORAGE_CONTAINER_NAME=documents \
    OPENAI_API_KEY="$OPENAI_API_KEY" \
    OPENAI_MODEL=gpt-3.5-turbo \
    POWER_AUTOMATE_URL="$POWER_AUTOMATE_URL" \
    POWER_AUTOMATE_SIGNATURE="$POWER_AUTOMATE_SIGNATURE" \
    ="$"

echo "✅ Deployment complete!"
echo "Get the URL with: az containerapp show -n $APP_NAME -g $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv"
echo ""
echo "📊 Auto-scaling configured:"
echo "   Min instances: $MIN_REPLICAS"
echo "   Max instances: $MAX_REPLICAS"
echo "   CPU per instance: ${CPU_REQUEST}"
echo "   RAM per instance: ${MEMORY_REQUEST}Gi"
echo ""
echo "To update auto-scaling later, use:"
echo "  MAX_REPLICAS=10 ./deploy-azure.sh"
echo ""
echo "To scale manually:"
echo "  az containerapp update -n $APP_NAME -g $RESOURCE_GROUP --min-replicas 2 --max-replicas 8"
