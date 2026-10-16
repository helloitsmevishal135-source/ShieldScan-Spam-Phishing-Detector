"""Admin trusted/blocked domain management — MongoDB version."""

from flask import flash, redirect, render_template, request, url_for

from app.admin.decorators import admin_required
from app.admin.services.log_helper import write_system_log
from app.admin import admin_bp
from app.ml.utils.url_normalize import registered_domain
from app.models import BlockedDomain, TrustedDomain
from app.services.trusted_domains import clear_trusted_domain_cache


def _normalize_domain(value: str) -> str:
    return registered_domain(value.strip().lower())


def _get_or_404(model, pk):
    """Fetch MongoEngine document by pk or abort 404."""
    from flask import abort
    try:
        obj = model.objects(pk=pk).first()
    except Exception:
        obj = None
    if not obj:
        abort(404)
    return obj


@admin_bp.route("/domains")
@admin_required
def domains():
    tab = request.args.get("tab", "trusted")
    q = (request.args.get("q") or "").strip().lower()

    if q:
        trusted = TrustedDomain.objects(domain__icontains=q).order_by("domain").limit(200)
        blocked = BlockedDomain.objects(domain__icontains=q).order_by("domain").limit(200)
    else:
        trusted = TrustedDomain.objects.order_by("domain").limit(200)
        blocked = BlockedDomain.objects.order_by("domain").limit(200)

    return render_template("admin/domains.html", tab=tab, q=q, trusted=trusted, blocked=blocked)


@admin_bp.route("/domains/trusted/add", methods=["POST"])
@admin_required
def add_trusted():
    domain = _normalize_domain(request.form.get("domain", ""))
    notes = (request.form.get("notes") or "").strip()[:512]
    if not domain:
        flash("Domain is required.", "warning")
        return redirect(url_for("admin.domains", tab="trusted"))

    if TrustedDomain.objects(domain=domain).first():
        flash("Domain already exists.", "warning")
        return redirect(url_for("admin.domains", tab="trusted"))

    TrustedDomain(domain=domain, notes=notes or None, is_active=True).save()
    clear_trusted_domain_cache()
    write_system_log("INFO", "system", f"Trusted domain added: {domain}")
    flash(f"Added trusted domain: {domain}", "success")
    return redirect(url_for("admin.domains", tab="trusted"))


@admin_bp.route("/domains/trusted/<domain_id>/edit", methods=["POST"])
@admin_required
def edit_trusted(domain_id: str):
    row = _get_or_404(TrustedDomain, domain_id)
    notes = (request.form.get("notes") or "").strip()[:512]
    is_active = request.form.get("is_active") == "on"
    row.notes = notes or None
    row.is_active = is_active
    row.save()
    clear_trusted_domain_cache()
    flash("Trusted domain updated.", "success")
    return redirect(url_for("admin.domains", tab="trusted"))


@admin_bp.route("/domains/trusted/<domain_id>/delete", methods=["POST"])
@admin_required
def delete_trusted(domain_id: str):
    row = _get_or_404(TrustedDomain, domain_id)
    row.delete()
    clear_trusted_domain_cache()
    flash("Trusted domain removed.", "info")
    return redirect(url_for("admin.domains", tab="trusted"))


@admin_bp.route("/domains/blocked/add", methods=["POST"])
@admin_required
def add_blocked():
    domain = _normalize_domain(request.form.get("domain", ""))
    reason = (request.form.get("reason") or "").strip()[:512]
    if not domain:
        flash("Domain is required.", "warning")
        return redirect(url_for("admin.domains", tab="blocked"))

    if BlockedDomain.objects(domain=domain).first():
        flash("Domain already blocked.", "warning")
        return redirect(url_for("admin.domains", tab="blocked"))

    BlockedDomain(domain=domain, reason=reason or None, is_active=True).save()
    write_system_log("INFO", "system", f"Blocked domain added: {domain}")
    flash(f"Added blocked domain: {domain}", "success")
    return redirect(url_for("admin.domains", tab="blocked"))


@admin_bp.route("/domains/blocked/<domain_id>/edit", methods=["POST"])
@admin_required
def edit_blocked(domain_id: str):
    row = _get_or_404(BlockedDomain, domain_id)
    reason = (request.form.get("reason") or "").strip()[:512]
    is_active = request.form.get("is_active") == "on"
    row.reason = reason or None
    row.is_active = is_active
    row.save()
    flash("Blocked domain updated.", "success")
    return redirect(url_for("admin.domains", tab="blocked"))


@admin_bp.route("/domains/blocked/<domain_id>/delete", methods=["POST"])
@admin_required
def delete_blocked(domain_id: str):
    row = _get_or_404(BlockedDomain, domain_id)
    row.delete()
    flash("Blocked domain removed.", "info")
    return redirect(url_for("admin.domains", tab="blocked"))
