terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Estado local — adequado para um desenvolvedor solo.
  # Para times, substitua por backend "gcs" ou "remote".
  backend "local" {}
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Usado para obter o project number sem hardcode
data "google_project" "project" {
  depends_on = [google_project_service.apis]
}

# ── APIs necessárias ──────────────────────────────────────────────────────────
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "firestore.googleapis.com",
  ])

  service            = each.key
  disable_on_destroy = false
}

# ── Service Account: Cloud Build ──────────────────────────────────────────────
resource "google_service_account" "cloudbuild" {
  account_id   = "sa-cloudbuild"
  display_name = "Cloud Build — Locadora Retrô"

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "cloudbuild_roles" {
  for_each = toset([
    "roles/run.admin",                # deploy no Cloud Run
    "roles/iam.serviceAccountUser",   # impersonate o SA do Cloud Run
    "roles/storage.admin",            # push imagens no Container Registry
    "roles/logging.logWriter",        # enviar logs ao Cloud Logging
    "roles/secretmanager.secretAccessor", # ler segredos no build (se necessário)
    "roles/artifactregistry.writer"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

# ── Service Account: Cloud Run ────────────────────────────────────────────────
resource "google_service_account" "cloudrun" {
  account_id   = "sa-cloudrun"
  display_name = "Cloud Run — Locadora Retrô"

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "cloudrun_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_project_iam_member" "cloudrun_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

# ── Firestore (Native mode) ───────────────────────────────────────────────────
# Pool de falas geradas pela IA — compartilhado entre instâncias e jogadores.
# Free tier: 1 GiB storage, 50K reads/dia, 20K writes/dia.
resource "google_firestore_database" "default" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.apis]
}

# ── Cloud Build service agent — acesso ao github-pat ─────────────────────────
# O agente interno do Cloud Build (service-NUMBER@gcp-sa-cloudbuild) precisa ler
# o PAT do GitHub para criar a conexão. Diferente do SA customizado sa-cloudbuild.
resource "google_secret_manager_secret_iam_member" "cloudbuild_agent_github_pat" {
  secret_id = "github-pat"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"

  depends_on = [google_project_service.apis]
}

# ── Cloud Run IAM público ─────────────────────────────────────────────────────
# ATENÇÃO: este recurso só pode ser aplicado APÓS o primeiro deploy do serviço.
# No primeiro terraform apply ele será ignorado (count=0).
# Após o primeiro deploy (git push master), defina first_deploy_done=true no tfvars
# e rode terraform apply novamente.
resource "google_cloud_run_service_iam_member" "public" {
  count    = var.first_deploy_done ? 1 : 0
 