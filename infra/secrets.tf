# ── Secret: Gemini API Key ────────────────────────────────────────────────────
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "gemini_api_key" {
  secret      = google_secret_manager_secret.gemini_api_key.id
  secret_data = var.gemini_api_key
}

# ── Secret: Flask Secret Key ──────────────────────────────────────────────────
resource "google_secret_manager_secret" "flask_secret_key" {
  secret_id = "flask-secret-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "flask_secret_key" {
  secret      = google_secret_manager_secret.flask_secret_key.id
  secret_data = var.flask_secret_key
}

# ── Secret: GitHub PAT (usado pelo Cloud Build v2 para conectar ao GitHub) ────
resource "google_secret_manager_secret" "github_pat" {
  secret_id = "github-pat"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "github_pat" {
  secret      = google_secret_manager_secret.github_pat.id
  secret_data = var.github_pat
}

# ── IAM: Cloud Build pode ler o PAT do GitHub ─────────────────────────────────
resource "google_secret_manager_secret_iam_member" "cloudbuild_github_pat" {
  secret_id = google_secret_manager_secret.github_pat.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudbuild.email}"
}
