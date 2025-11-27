#!/bin/bash

# Dashboard Metrics Kubernetes Deployment Script
# This script deploys the dashboard metrics cron job to Kubernetes

set -e

echo "🚀 Deploying Dashboard Metrics CronJob to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we're connected to the cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Not connected to any Kubernetes cluster"
    exit 1
fi

echo "✅ Connected to Kubernetes cluster"

# Apply the ConfigMap
echo "📋 Creating ConfigMap..."
kubectl apply -f k8s-configmap.yaml

# Apply the Secret
echo "🔐 Creating Secret..."
kubectl apply -f k8s-secret.yaml

# Create image pull secret if it doesn't exist
echo "📦 Setting up image pull secret..."
if ! kubectl get secret acr-secret &> /dev/null; then
    echo "Creating ACR secret..."
    # Replace with your actual ACR credentials
    kubectl create secret docker-registry acr-secret \
        --docker-server=zinfradevv1.azurecr.io \
        --docker-username=<ACR_USERNAME> \
        --docker-password=<ACR_PASSWORD> \
        --docker-email=<ACR_EMAIL>
else
    echo "ACR secret already exists"
fi

# Apply the CronJob
echo "⏰ Creating CronJob..."
kubectl apply -f k8s-cronjob-dashboard-metrics.yaml

# Verify deployment
echo "✅ Verifying deployment..."
kubectl get cronjob dashboard-metrics
kubectl get configmap dashboard-metrics-config
kubectl get secret dashboard-metrics-secrets

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 CronJob Details:"
echo "   - Name: dashboard-metrics"
echo "   - Schedule: */15 * * * * (every 15 minutes)"
echo "   - Namespace: default"
echo ""
echo "🔍 To monitor the cronjob:"
echo "   kubectl get cronjob dashboard-metrics"
echo "   kubectl get jobs -l app=dashboard-metrics"
echo "   kubectl get pods -l app=dashboard-metrics"
echo ""
echo "📝 To view logs:"
echo "   kubectl logs -l app=dashboard-metrics"
echo ""
echo "🧪 To test manually:"
echo "   kubectl create job --from=cronjob/dashboard-metrics dashboard-metrics-manual-$(date +%s)"