output "cloudbuild_trigger_name" {
  description = "Nome do trigger Cloud Build criado"
  value       = google_cloudbuild_trigger.deploy_on_push.name
}

output "cloudbuild_sa_email" {
  description = "Service Account usada pelo Cloud Build"
  value       = google_service_account.cloudbuild.email
}

output "cloudrun_sa_email" {
  description = "Service Account usada pelo Cloud Run"
  value       = google_service_account.cloudrun.email
}

output "github_connection_name" {
  description = "Nome da conexão Cloud Build v2 com o GitHub"
  value       = google_cloudbuildv2_connection.github.name
}

output "next_steps" {
  description = "Próximos passos após o primeiro apply"
  value       = <<-EOT
    ─────────────────────────────────────────────────────────────
    Infraestrutura provisionada. Próximos passos:

    1. Faça o primeiro deploy manual para criar o serviço Cloud Run:
         cd ..
         gcloud builds submit --tag gcr.io/${var.project_id}/${var.service_name}:latest .
         gcloud run deploy ${var.service_name} \
           --image gcr.io/${var.project_id}/${var.service_name}:latest \
           --region ${var.region} \
           --platform managed \
           --allow-unauthenticated \
           --service-account sa-cloudrun@${var.project_id}.iam.gserviceaccount.com \
           --set-secrets GEMINI_API_KEY=gemini-api-key:latest,SECRET_KEY=flask-secret-key:latest \
           --set-env-vars LLM_PROVIDER=gemini,LLM_MODEL=${var.llm_model}

    2. Após o primeiro deploy, rode novamente:
         terraform apply
       (para garantir o IAM público do Cloud Run)

    3. A partir daí, qualquer push na branch master dispara o pipeline automaticamente.
    ─────────────────────────────────────────────────�