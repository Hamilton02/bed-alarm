#!/bin/sh
# Redeploy to Cloud Run on the personal project. Secrets live in Secret Manager
# (bed-sleepiq-email, bed-sleepiq-password, bed-token); runtime SA can read only those.
set -e
P=dannywalshdev
gcloud run deploy bed-alarm --source "$(dirname "$0")" --project $P --region us-west1 \
  --service-account bed-alarm-run@$P.iam.gserviceaccount.com --allow-unauthenticated \
  --set-env-vars SLEEPER=R,WAKE_NUMBER=100 \
  --set-secrets SLEEPIQ_EMAIL=bed-sleepiq-email:latest,SLEEPIQ_PASSWORD=bed-sleepiq-password:latest,BED_TOKEN=bed-token:latest \
  --memory 256Mi --max-instances 1 --quiet
