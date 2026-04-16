"""
analyzer/tasks.py
=================
Celery tasks for Ingrexa's heavy background operations.

Why this file exists
--------------------
The two most expensive operations in the app are:

  1. analyze_ingredients  — calls GPT-4o-mini + IngredientScorer (~3-12 s)
  2. send_contact_email   — SMTP / HTTP to Resend         (~1-5 s)

Running these synchronously inside a Django view blocks a Gunicorn worker
for the entire duration.  With Celery + Redis each view returns a task_id
in ~5 ms, and the heavy work runs in a separate worker process.

Task result lifecycle
---------------------
Results are stored in Redis for CELERY_TASK_RESULT_EXPIRES (default 1 hour).
The frontend polls  GET /api/task/<task_id>/  to check progress.

Retry strategy
--------------
Both tasks retry up to 3 times with exponential back-off so transient
OpenAI / SMTP failures are handled automatically without user involvement.
"""

import os
import traceback
from celery import shared_task


# ─────────────────────────────────────────────────────────────────────────────
# Task 1: AI Ingredient Analysis
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(
    bind=True,
    name="analyzer.tasks.analyze_ingredients_task",
    max_retries=3,
    default_retry_delay=10,   # seconds before first retry
    acks_late=True,           # Only ack after the task finishes (safer)
    reject_on_worker_lost=True,
)
def analyze_ingredients_task(
    self,
    text: str,
    macros: dict,
    food_type: str,
    user_goal: str,
    user_id: int | None = None,
    input_method: str = "manual",
    barcode: str = "",
    product_info: dict | None = None,
):
    """
    Run the full ingredient analysis pipeline in a Celery worker.

    Parameters
    ----------
    text          : Raw ingredient text to analyze.
    macros        : Nutriment dict from OpenFoodFacts (can be empty).
    food_type     : 'Solid' | 'Liquid' | 'Semi-solid'
    user_goal     : 'Regular' | 'Weight Loss' | 'Muscle Gain' | ...
    user_id       : Django User PK — used to save AnalysisRecord afterward.
    input_method  : 'manual' | 'openfoodfacts' | 'barcode'
    barcode       : Barcode string (for AnalysisRecord).
    product_info  : Enriched product dict from OpenFoodFacts (optional).

    Returns
    -------
    dict  — the full analysis_result dict (same shape as the sync views).
    """
    from .ai_service import analyze_product_from_text
    from .models import AnalysisRecord

    try:
        print(
            f"[CELERY] analyze_ingredients_task started | method={input_method} "
            f"food_type={food_type} user_goal={user_goal} user_id={user_id}"
        )

        # ── Core analysis ──────────────────────────────────────────────────
        analysis_result = analyze_product_from_text(
            text=text,
            macros=macros or {},
            food_type=food_type,
            user_goal=user_goal,
        )

        # ── Enrich with product metadata from OpenFoodFacts ────────────────
        if product_info:
            analysis_result["product_info"] = product_info
            analysis_result.setdefault("product", {})
            analysis_result["product"]["name"] = product_info.get(
                "name", analysis_result["product"].get("name", "Unknown")
            )
            analysis_result["product"]["brand"] = product_info.get("brand", "Unknown")
            analysis_result["product"]["image_url"] = product_info.get("image_url", "")
            analysis_result["product"]["nutriscore_grade"] = product_info.get(
                "nutriscore_grade", ""
            )
            analysis_result["_product_meta"] = {
                "name": product_info.get("name", ""),
                "brand": product_info.get("brand", ""),
                "image_url": product_info.get("image_url", ""),
                "categories": product_info.get("categories", ""),
                "nutriscore_grade": product_info.get("nutriscore_grade", ""),
                "barcode": barcode,
                "nutriments": product_info.get("nutriments"),
            }

        analysis_result["input_method"] = input_method
        analysis_result["raw_ingredients_text"] = text

        # ── Persist AnalysisRecord for authenticated users ─────────────────
        if user_id:
            try:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                user = User.objects.get(pk=user_id)
                product_data = analysis_result.get("product", {}) or {}
                analysis_for_storage = {
                    k: v
                    for k, v in analysis_result.items()
                    if k != "raw_ingredients_text"
                }
                AnalysisRecord.objects.create(
                    user=user,
                    input_method=(
                        AnalysisRecord.INPUT_BARCODE
                        if barcode
                        else AnalysisRecord.INPUT_TEXT
                    ),
                    input_text_preview=text.strip()[:400],
                    product_name=product_data.get("name", ""),
                    product_brand=product_data.get("brand", ""),
                    user_goal=user_goal,
                    food_type=food_type,
                    confidence=analysis_result.get("confidence"),
                    score=analysis_result.get("score"),
                    nova_group=analysis_result.get("nova_group"),
                    nutriscore_grade=product_data.get("nutriscore_grade", "") or "",
                    analysis_json=analysis_for_storage,
                )
                print(f"[CELERY] AnalysisRecord saved for user {user_id}")
            except Exception as db_err:
                # Don't fail the task if DB write fails
                print(f"[CELERY] Could not save AnalysisRecord: {db_err}")

        print("[CELERY] analyze_ingredients_task completed successfully")
        return analysis_result

    except Exception as exc:
        print(f"[CELERY] analyze_ingredients_task error: {type(exc).__name__}: {exc}")
        print(traceback.format_exc())
        # Retry with exponential back-off: 10s, 20s, 40s
        raise self.retry(exc=exc, countdown=10 * (2 ** self.request.retries))


# ─────────────────────────────────────────────────────────────────────────────
# Task 2: Send Contact Email
# ─────────────────────────────────────────────────────────────────────────────

@shared_task(
    bind=True,
    name="analyzer.tasks.send_contact_email_task",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def send_contact_email_task(self, name: str, email: str, message: str):
    """
    Send a contact-form email in the background.

    Tries Django SMTP first, falls back to Resend HTTP API.
    Retries up to 3 times on any failure.

    Parameters
    ----------
    name    : Sender's name (already HTML-escaped by the view).
    email   : Sender's email address.
    message : Message body (already HTML-escaped by the view).
    """
    from django.core.mail import send_mail

    from_email = os.environ.get("EMAIL_HOST_USER", "")
    to_email = os.environ.get("CONTACT_EMAIL_RECIPIENT", from_email)
    subject = f"New Contact Message from {name}"
    body = (
        f"New contact message from Ingrexa:\n\n"
        f"From: {name}\n"
        f"Email: {email}\n\n"
        f"Message:\n{message}\n\n"
        f"---\nSent from Ingrexa Contact Form"
    )

    email_sent = False

    # ── Primary: Django SMTP ───────────────────────────────────────────────
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False,
        )
        email_sent = True
        print(f"[CELERY] Contact email sent via SMTP to {to_email}", flush=True)
    except Exception as smtp_err:
        print(f"[CELERY] SMTP failed: {smtp_err}. Trying Resend…", flush=True)

    # ── Fallback: Resend HTTP API ──────────────────────────────────────────
    if not email_sent:
        try:
            import requests as http_requests

            resend_api_key = os.environ.get("RESEND_API_KEY", "")
            if resend_api_key:
                resp = http_requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": "Ingrexa Contact <onboarding@resend.dev>",
                        "to": [to_email],
                        "subject": subject,
                        "text": body,
                    },
                    timeout=15,
                )
                print(f"[CELERY] Resend response: {resp.status_code}", flush=True)
                email_sent = resp.status_code == 200
            else:
                print("[CELERY] No Resend API key. Email not sent.", flush=True)
        except Exception as resend_err:
            print(f"[CELERY] Resend also failed: {resend_err}", flush=True)
            raise self.retry(exc=resend_err, countdown=30 * (2 ** self.request.retries))

    return {"sent": email_sent, "to": to_email}
