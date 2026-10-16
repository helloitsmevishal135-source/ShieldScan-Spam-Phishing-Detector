"""Admin model management routes — MongoDB version."""

import json
from pathlib import Path

from flask import flash, redirect, render_template, request, send_file, url_for

from app.admin.decorators import admin_required, get_current_admin
from app.admin.services.log_helper import write_system_log
from app.admin.services.model_manager import (
    deploy_model_version,
    get_phishing_feature_importance,
    save_uploaded_dataset,
    train_phishing_model,
    train_spam_model,
)
from app.admin import admin_bp
from app.models import ModelVersion, TrainingLog


def _get_or_404(model, pk):
    from flask import abort
    try:
        obj = model.objects(pk=pk).first()
    except Exception:
        obj = None
    if not obj:
        abort(404)
    return obj


@admin_bp.route("/models")
@admin_required
def models():
    versions = ModelVersion.objects.order_by("-created_at").limit(50)
    training_logs = TrainingLog.objects.order_by("-created_at").limit(20)
    feature_importance = get_phishing_feature_importance()
    top_features = sorted(feature_importance.items(), key=lambda item: item[1], reverse=True)[:15]
    return render_template(
        "admin/models.html",
        versions=versions,
        training_logs=training_logs,
        top_features=top_features,
    )


@admin_bp.route("/models/upload", methods=["POST"])
@admin_required
def upload_dataset():
    dataset_type = request.form.get("dataset_type", "")
    file = request.files.get("dataset_file")
    if not file or not file.filename:
        flash("Choose a CSV file to upload.", "warning")
        return redirect(url_for("admin.models"))

    try:
        path = save_uploaded_dataset(file, dataset_type)
        write_system_log("INFO", "training", f"Dataset uploaded: {dataset_type}", {"path": str(path)})
        flash(f"Dataset uploaded to {path.name}.", "success")
    except Exception as exc:
        write_system_log("ERROR", "training", f"Dataset upload failed: {exc}")
        flash(str(exc), "danger")
    return redirect(url_for("admin.models"))


@admin_bp.route("/models/train/<model_type>", methods=["POST"])
@admin_required
def train_model(model_type: str):
    admin = get_current_admin()
    try:
        if model_type == "spam":
            result = train_spam_model(trained_by=admin.username if admin else None)
        elif model_type == "phishing":
            result = train_phishing_model(trained_by=admin.username if admin else None)
        else:
            flash("Unknown model type.", "danger")
            return redirect(url_for("admin.models"))

        metrics = result["metrics"]
        write_system_log(
            "INFO",
            "training",
            f"Model trained: {result['model_name']} v{result['version']}",
            {"metrics": metrics},
        )
        flash(
            f"Training complete — Accuracy {metrics['accuracy']:.2%}, F1 {metrics['f1_score']:.2%}",
            "success",
        )
    except Exception as exc:
        write_system_log("ERROR", "training", f"Training failed ({model_type}): {exc}")
        flash(f"Training failed: {exc}", "danger")
    return redirect(url_for("admin.models"))


@admin_bp.route("/models/deploy/<version_id>", methods=["POST"])
@admin_required
def deploy_model(version_id: str):
    try:
        row = deploy_model_version(version_id)
        write_system_log("INFO", "training", f"Deployed model {row.model_name} v{row.version}")
        flash(f"Deployed {row.model_name} version {row.version}.", "success")
    except Exception as exc:
        flash(str(exc), "danger")
    return redirect(url_for("admin.models"))


@admin_bp.route("/models/download/<version_id>")
@admin_required
def download_model(version_id: str):
    row = _get_or_404(ModelVersion, version_id)
    path = Path(row.artifact_path)
    if not path.exists():
        flash("Model artifact not found on disk.", "danger")
        return redirect(url_for("admin.models"))
    return send_file(path, as_attachment=True, download_name=path.name)


@admin_bp.route("/models/metrics/<log_id>")
@admin_required
def training_metrics(log_id: str):
    row = _get_or_404(TrainingLog, log_id)
    try:
        metrics = json.loads(row.metrics_json)
    except json.JSONDecodeError:
        metrics = {}
    return render_template("admin/training_metrics.html", log=row, metrics=metrics)
