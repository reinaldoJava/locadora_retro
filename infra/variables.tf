variable "project_id" {
  description = "ID do projeto GCP (ex: locadora-retro-123456)"
  type        = string
}

variable "region" {
  description = "Região do Cloud Run e Cloud Build"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Nome do serviço Cloud Run"
  type        = string
  default     = "locadora-retro"
}

variable "llm_model" {
  description = "Modelo Gemini usado em produção"
  type        = string
  default     = "gemini-3.1-flash-lite"
}

# ── GitHub ────────────────────────────────────────────────────────────────────
variable "github_owner" {
  description = "Owner da organização ou usuário no GitHub (ex: reinaldo)"
  type        = string
}

variable "github_repo_name" {
  description = "Nome do repositório no GitHub (ex: Locadora-Retro)"
  type        = string
}

variable "github_pat" {
  description = <<-EOT
    Personal Access Token do GitHub com escopos:
      - repo (leitura do código)
      - read:user
      - read:org  (se o repo for de uma organização)
    Crie em: https://github.com/settings/tokens
  EOT
  type        = string
  sensitive   = true
}

variable "github_app_installation_id" {
  description = <<-EOT
    ID de instalação do GitHub App "Google Cloud Build".
    Como obter:
      1. Acesse https://github.com/apps/google-cloud-build → Configure
      2. Autorize para o seu usuário/org e repositório
      3. Após redirecionar, copie o número da URL:
         https://github.com/settings/installations/XXXXXXXX
  EOT
  type = number
  default = "135484543"
}

# ── Segredos da aplicação ─────────────────────────────────────────────────────
variable "first_deploy_done" {
  description = "Defina como true após o primeiro deploy do Cloud Run para habilitar o IAM público."
  type        = bool
  default     = false
}

variable "gemini_api_key" {
  description = "Chave da API Gemini (Google AI Studio: https://aistudio.google.com/app/apikey)"
  type        = string
  sensitive   = true
}

variable "flask_secret_key" {
  description = "Chave secreta do Flask para assinar sessões. Gere com: python3 -c 'import secrets; prin