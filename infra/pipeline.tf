# ── Cloud Build v2: Conexão com GitHub ───────────────────────────────────────
#
# ATENÇÃO: Esta conexão deve ser criada manualmente no console GCP (fluxo OAuth)
# e depois importada para o state do Terraform:
#
#   1. Console → Cloud Build → Repositórios (2ª geração) → Criar conexão de host
#   2. Selecione GitHub e siga o fluxo OAuth
#   3. Nomeie a conexão como "github-locadora-retro"
#   4. Após criar, importe:
#      terraform import google_cloudbuildv2_connection.github \
#        projects/PROJECT_ID/locations/REGION/connections/github-locadora-retro
#
# O recurso abaixo gerencia a conexão após o import (não tenta recriar).
resource "google_cloudbuildv2_connection" "github" {
  name     = "github-locadora-retro"
  location = var.region

  github_config {
    app_installation_id = var.github_app_installation_id
    authorizer_credential {
      oauth_token_secret_version = google_secret_manager_secret_version.github_pat.id
    }
  }

  lifecycle {
    ignore_changes = [github_config]
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_iam_member.cloudbuild_agent_github_pat,
  ]
}

# ── Cloud Build v2: Repositório vinculado ─────────────────────────────────────
resource "google_cloudbuildv2_repository" "locadora_retro" {
  name              = var.github_repo_name
  location          = var.region
  parent_connection = google_cloudbuildv2_connection.github.id
  remote_uri        = "https://github.com/${var.github_owner}/${var.github_repo_name}.git"
}

# ── Cloud Build Trigger: push na branch master → deploy ──────────────────────
resource "google_cloudbuild_trigger" "deploy_on_push" {
  name        = "deploy-on-push-master"
  description = "Locadora Retrô — deploy automático a cada push na branch master"
  location    = var.region

  repository_event_config {
    repository = google_cloudbuildv2_repository.locadora_retro.id

    push {
      branch = "^master$"
    }
  }

  # Usa o cloudbuild.yaml na raiz do repositório
  filename = "cloudbuild.yaml"

  substitutions = {
    _REGION      = var.region
    _SERVICE     = var.service_name
    _LLM_MODEL   = var.llm_model
  }

  service_account = google_service_account.cloudbuild.id

  depends_on = [
    google_project_iam_member.cloudbuild_roles,
    google_cloudbuildv2_repository.locadora_retro,
  ]
}
