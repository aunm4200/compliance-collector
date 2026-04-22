// -----------------------------------------------------------------------------
// compliance-collector v0.6 — Azure hosting for demo
//
// Provisions the resources needed to demo the portal + backend to real tenants:
//   * Log Analytics workspace
//   * Container Apps Environment
//   * User-assigned Managed Identity (used as Graph FIC assertion source)
//   * Azure Container Registry (Basic) with AcrPull granted to the UAMI
//   * Container App running the FastAPI backend
//   * Container App running the Next.js portal
//
// Cost target: ~$15–40/month at demo scale (min 0 / max 2 replicas per app).
// -----------------------------------------------------------------------------

@description('Deployment region.')
param location string = resourceGroup().location

@description('Short prefix (lowercase, <=8 chars) for resource names.')
@maxLength(8)
param namePrefix string = 'ccol'

@description('Backend container image reference (e.g. myregistry.azurecr.io/backend:0.6.0).')
param backendImage string

@description('Portal container image reference (e.g. myregistry.azurecr.io/portal:0.6.0).')
param portalImage string

@description('Our multi-tenant Entra app client ID.')
param entraAppClientId string

@description('API audience, typically api://<client_id>.')
param entraApiAudience string

@description('API scope the portal requests (e.g. api://<client_id>/access_as_user).')
param entraApiScope string

var uniq = toLower(uniqueString(resourceGroup().id))
var shortName = '${namePrefix}${substring(uniq, 0, 6)}'
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

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

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, uami.id, acrPullRoleId)
  scope: acr
  properties: {
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
  }
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

var backendAppName = '${shortName}-api'
var portalAppName = '${shortName}-web'
var backendFqdn = '${backendAppName}.${cae.properties.defaultDomain}'
var portalFqdn = '${portalAppName}.${cae.properties.defaultDomain}'
var backendUrl = 'https://${backendFqdn}'
var portalUrl = 'https://${portalFqdn}'

resource backend 'Microsoft.App/containerApps@2024-03-01' = {
  name: backendAppName
  location: location
  dependsOn: [ acrPull ]
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
        corsPolicy: {
          allowedOrigins: [ portalUrl ]
          allowedMethods: [ 'GET', 'POST', 'OPTIONS' ]
          allowedHeaders: [ '*' ]
          allowCredentials: false
        }
      }
      registries: [
        {
          server: acr.properties.loginServer
          identity: uami.id
        }
      ]
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
            { name: 'STORAGE_LOCAL_PATH', value: '/app/evidence_store' }
            { name: 'CORS_ALLOW_ORIGINS', value: string([portalUrl]) }
          ]
        }
      ]
      scale: { minReplicas: 0, maxReplicas: 2 }
    }
  }
}

resource portal 'Microsoft.App/containerApps@2024-03-01' = {
  name: portalAppName
  location: location
  dependsOn: [ acrPull ]
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
        targetPort: 3000
        transport: 'auto'
      }
      registries: [
        {
          server: acr.properties.loginServer
          identity: uami.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'portal'
          image: portalImage
          resources: { cpu: json('0.25'), memory: '0.5Gi' }
          env: [
            { name: 'NODE_ENV', value: 'production' }
            { name: 'NEXT_PUBLIC_BACKEND_URL', value: backendUrl }
            { name: 'NEXT_PUBLIC_ENTRA_CLIENT_ID', value: entraAppClientId }
            { name: 'NEXT_PUBLIC_ENTRA_API_SCOPE', value: entraApiScope }
            { name: 'NEXT_PUBLIC_ENTRA_REDIRECT_URI', value: '${portalUrl}/auth/callback' }
            { name: 'NEXT_PUBLIC_DEV_BYPASS_AUTH', value: 'false' }
          ]
        }
      ]
      scale: { minReplicas: 0, maxReplicas: 2 }
    }
  }
}

output backendUrl string = backendUrl
output portalUrl string = portalUrl
output backendAppName string = backend.name
output portalAppName string = portal.name
output uamiClientId string = uami.properties.clientId
output uamiPrincipalId string = uami.properties.principalId
output uamiResourceId string = uami.id
output acrName string = acr.name
output acrLoginServer string = acr.properties.loginServer
