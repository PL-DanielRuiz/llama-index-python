targetScope = 'resourceGroup'

@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Flag to decide where to create OpenAI role for current user')
param createRoleForUser bool = true

@description('Flag to decide whether to create Azure OpenAI instance or not')
param createAzureOpenAi bool // Set in main.parameters.json

param llamaIndexPythonExists bool
@secure()
param llamaIndexPythonDefinition object

@description('Id of the user or app to assign application roles')
param principalId string

param openAiLocation string // Set in main.parameters.json
param openAiSkuName string = 'S0' // Set in main.parameters.json
param openAiUrl string = '' // Set in main.parameters.json
param openAiApiVersion string // Set in main.parameters.json

var finalOpenAiUrl = empty(openAiUrl) ? 'https://${openAi.outputs.name}.openai.azure.com' : openAiUrl


var systemPrompt = 'You are a helpful assistant who specializes in providing precise and accurate answers based on the information contained in a set of provided manuals. Your task is to assist users by answering their questions with the highest degree of accuracy, drawing directly from the content of these manuals. When responding to a question: [1] Accuracy: Provide answers that are directly supported by the manuals, without interpretation or added information. If the answer is not explicitly stated in the manuals, explain that the information is not available. [2] Conciseness: Give brief and to-the-point responses, only including details that are relevant and necessary to answer the question. [3] Source Identification: Whenever possible, reference the specific section or page of the manual from which the information is derived. [4] Clarifications: If the question is unclear or ambiguous, ask the user for clarification before providing an answer. [5] Response Format: Structure your responses in a clear, logical manner that is easy for the user to understand.'

var llamaIndexConfig = {
  chat: {
    model: 'gpt-35-turbo'
    deployment: 'gpt-35-turbo'
    version: '1106'
    capacity: '10'
  }
  embedding: {
    model: 'text-embedding-ada-002' //'text-embedding-3-large'
    deployment: 'text-embedding-ada-002' //'text-embedding-3-large'
    dim: '1024'
    capacity: '10'
  }
  model_provider: 'azure-openai'
  openai_api_key: ''
  llm_temperature: '0.0'
  llm_max_tokens: '500'
  top_k: '5'
  fileserver_url_prefix: 'http://localhost/api/files'
  system_prompt: systemPrompt
}

var tags = {
  'azd-env-name': environmentName
}

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(resourceGroup().id, environmentName, location))

module monitoring './shared/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    location: location
    tags: tags
    logAnalyticsName: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: '${abbrs.insightsComponents}${resourceToken}'
  }
  scope: resourceGroup()
}

module dashboard './shared/dashboard-web.bicep' = {
  name: 'dashboard'
  params: {
    name: '${abbrs.portalDashboards}${resourceToken}'
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    location: location
    tags: tags
  }
  scope: resourceGroup()
}

module registry './shared/registry.bicep' = {
  name: 'registry'
  params: {
    location: location
    tags: tags
    name: '${abbrs.containerRegistryRegistries}${resourceToken}'
  }
  scope: resourceGroup()
}

module keyVault './shared/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    location: location
    tags: tags
    name: '${abbrs.keyVaultVaults}${resourceToken}'
    principalId: principalId
  }
  scope: resourceGroup()
}

module appsEnv './shared/apps-env.bicep' = {
  name: 'apps-env'
  params: {
    name: '${abbrs.appManagedEnvironments}${resourceToken}'
    location: location
    tags: tags
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    logAnalyticsWorkspaceName: monitoring.outputs.logAnalyticsWorkspaceName
  }
  scope: resourceGroup()
}

module openAi './shared/cognitiveservices.bicep' = if (empty(openAiUrl)) {
  name: 'openai'
  scope: resourceGroup()
  params: {
    name: '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    location: openAiLocation
    tags: tags
    sku: {
      name: openAiSkuName
    }
    disableLocalAuth: true
    deployments: [
      {
        name: llamaIndexConfig.chat.deployment
        model: {
          format: 'OpenAI'
          name: llamaIndexConfig.chat.model
          version: llamaIndexConfig.chat.version
        }
        sku: {
          name: 'Standard'
          capacity: llamaIndexConfig.chat.capacity
        }
      }
      {
        name: llamaIndexConfig.embedding.model
        model: {
          format: 'OpenAI'
          name: llamaIndexConfig.embedding.deployment
        }
        capacity: llamaIndexConfig.embedding.capacity
      }
    ]
  }
}

module openAiRoleUser './shared/role.bicep' = if (createRoleForUser && createAzureOpenAi) {
  scope: resourceGroup()
  name: 'openai-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'User'
  }
}

module openAiRoleBackend './shared/role.bicep' = if (createAzureOpenAi && !createRoleForUser) {
  scope: resourceGroup()
  name: 'openai-role-backend'
  params: {
    principalId: principalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'ServicePrincipal'
  }
}

module llamaIndexPython './app/llama-index-python.bicep' = {
  name: 'llama-index-python'
  params: {
    name: '${abbrs.appContainerApps}llama-index-${resourceToken}'
    location: location
    tags: tags
    identityName: '${abbrs.managedIdentityUserAssignedIdentities}llama-index-${resourceToken}'
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    containerAppsEnvironmentName: appsEnv.outputs.name
    containerRegistryName: registry.outputs.name
    exists: llamaIndexPythonExists
    appDefinition: union(llamaIndexPythonDefinition, {
      settings: [
        {
          name: 'AZURE_KEY_VAULT_NAME' 
          value: keyVault.outputs.name
        }
        {
          name: 'AZURE_KEY_VAULT_ENDPOINT' 
          value: keyVault.outputs.endpoint
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT' 
          value: finalOpenAiUrl
        }
        {
          name: 'AZURE_DEPLOYMENT_NAME' 
          value: llamaIndexConfig.chat.deployment
        }
        {
          name: 'OPENAI_API_VERSION' 
          value: openAiApiVersion
        }
        {
          name: 'MODEL_PROVIDER' 
          value: llamaIndexConfig.model_provider
        }
        {
          name: 'MODEL' 
          value: llamaIndexConfig.chat.model
        }
        {
          name: 'EMBEDDING_MODEL' 
          value: llamaIndexConfig.embedding.model
        }
        {
          name: 'EMBEDDING_DIM' 
          value: llamaIndexConfig.embedding.dim
        }
        {
          name: 'LLM_TEMPERATURE' 
          value: llamaIndexConfig.llm_temperature
        }
        {
          name: 'LLM_MAX_TOKENS' 
          value: llamaIndexConfig.llm_max_tokens
        }
        {
          name: 'TOP_K' 
          value: llamaIndexConfig.top_k
        }
        {
          name: 'FILESERVER_URL_PREFIX' 
          value: llamaIndexConfig.fileserver_url_prefix
        }
        {
          name: 'SYSTEM_PROMPT' 
          value: llamaIndexConfig.system_prompt
        }
      ]
    })
  }
  scope: resourceGroup()
}

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = registry.outputs.loginServer
output AZURE_KEY_VAULT_NAME string = keyVault.outputs.name
output AZURE_KEY_VAULT_ENDPOINT string = keyVault.outputs.endpoint

output AZURE_OPENAI_ENDPOINT string = finalOpenAiUrl
output AZURE_DEPLOYMENT_NAME string = llamaIndexConfig.chat.deployment
output OPENAI_API_VERSION string = openAiApiVersion

output MODEL_PROVIDER string = llamaIndexConfig.model_provider
