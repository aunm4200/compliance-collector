// -----------------------------------------------------------------------------
// compliance-collector v0.4 — minimal Azure infrastructure
//
// Provisions the resources the backend needs for a single-environment MVP:
//   * Log Analytics workspace
//   * Container Apps Environment
//   * User-assigned Managed Identity (used as Graph FIC assertion source)
//   * Azure Container Registry (Basic)
//   * Container App running the backend image
//
// v0.5 will extend this with Cosmos DB, Storage account, Key Vault, and
// Azure Static Web Apps for the UI.
// -----------------------------------------------------------------------------

@description('Deployment region.')
param location string = resourceGroup().location

@description('Short prefix (lowercase, <=8 chars) for resource names.')
@maxLength(8)
param namePrefix string = 'ccol'

@description('Container image reference (e.g. myregistry.azurecr.io/backend:0.4.0).')
param backendImage string

@description('Our multi-tenant Entra app client ID.')
param entraAppClientId string

@description('API audience, typically api://<client_id>.')
param entraApiAudience string

var uniq = toLower(uniqueString(resourceGroup().id))
var shortName = '${namePrefix}${substring(uniq, 0, 6)}'

resource law 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${shortName}-law'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${shortName}-uami'
  location: location
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: '${shortName}acr'
  location: location
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: false }
}

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${shortName}-cae'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: law.listKeys().primarySharedKey
      }
    }
  }
}

resource backend 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${shortName}-api'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uami.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: cae.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: backendImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'ENVIRONMENT', value: 'prod' }
            { name: 'GRAPH_AUTH_MODE', value: 'mi_fic' }
            { name: 'GRAPH_MANAGED_IDENTITY_CLIENT_ID', value: uami.properties.clientId }
            { name: 'ENTRA_APP_CLIENT_ID', value: entraAppClientId }
            { name: 'ENTRA_APP_TENANT_ID', value: 'common' }
            { name: 'ENTRA_API_AUDIENCE', value: entraApiAudience }
            { name: 'STORAGE_BACKEND', value: 'local' }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}

output backendFqdn string = backend.properties.configuration.ingress.fqdn
output uamiClientId string = uami.properties.clientId
output uamiPrincipalId string = uami.properties.principalId
output acrLoginServer string = acr.properties.loginServer
