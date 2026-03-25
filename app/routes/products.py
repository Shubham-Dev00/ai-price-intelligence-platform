from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.forms import ProductForm, ProductEditForm
from app.models import TrackedProduct, PriceSnapshot, ProductInsight, AlertEvent, ScrapeAttempt
from app.services.product_service import ProductService
from app.services.analytics_service import AnalyticsService
from app.utils.helpers import normalize_url

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("/", methods=["GET", "POST"])
@login_required
def list_products():
    form = ProductForm()
    products = current_user.products.order_by(TrackedProduct.created_at.desc()).all()
    duplicates = []

    if form.validate_on_submit():
        existing = TrackedProduct.query.filter_by(
            user_id=current_user.id,
            normalized_url=normalize_url(form.product_url.data)
        ).first()
        if existing:
            flash("This product is already being tracked in your account.", "warning")
            return redirect(url_for("products.list_products"))

        product, scrape_result, duplicates = ProductService.add_product_for_user(
            current_user,
            form.product_url.data,
            title_override=form.title.data or None,
            target_price=form.target_price.data,
            is_tracking_enabled=form.is_tracking_enabled.data,
        )
        if not product:
            flash(scrape_result.error_message or "Could not add product.", "danger")
        else:
            if scrape_result.success:
                flash("Product added successfully.", "success")
            else:
                flash(
                    "Product was saved using manual fallback. Live price could not be verified yet, so background refresh can retry later.",
                    "warning",
                )
            if duplicates:
                flash("Potential duplicate products were detected in your account.", "warning")
            return redirect(url_for("products.list_products"))
    return render_template("products/list.html", form=form, products=products, duplicates=duplicates)


@products_bp.route("/<int:product_id>", methods=["GET", "POST"])
@login_required
def detail(product_id):
    product = TrackedProduct.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    form = ProductEditForm(obj=product)
    if form.validate_on_submit():
        product.title = form.title.data
        product.target_price = form.target_price.data
        product.is_tracking_enabled = form.is_tracking_enabled.data
        db.session.commit()
        flash("Product updated.", "success")
        return redirect(url_for("products.detail", product_id=product.id))

    metrics = AnalyticsService.get_price_metrics(product)
    snapshots = product.price_snapshots.order_by(PriceSnapshot.captured_at.asc()).all()
    insights = product.insights.order_by(ProductInsight.generated_at.desc()).all()
    alert_history = product.alert_events.order_by(AlertEvent.triggered_at.desc()).all()
    scrape_attempts = product.scrape_attempts.order_by(ScrapeAttempt.attempted_at.desc()).limit(10).all()

    chart_labels = [snapshot.captured_at.strftime("%Y-%m-%d %H:%M") for snapshot in snapshots]
    chart_values = [snapshot.price for snapshot in snapshots]

    return render_template(
        "products/detail.html",
        product=product,
        form=form,
        metrics=metrics,
        snapshots=snapshots,
        insights=insights,
        alert_history=alert_history,
        scrape_attempts=scrape_attempts,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


@products_bp.post("/<int:product_id>/refresh")
@login_required
def refresh(product_id):
    product = TrackedProduct.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    result = ProductService.refresh_product(product)
    flash("Product refreshed successfully." if result.success else f"Refresh failed: {result.error_message}", "info")
    return redirect(url_for("products.detail", product_id=product.id))


@products_bp.post("/<int:product_id>/delete")
@login_required
def delete(product_id):
    product = TrackedProduct.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "success")
    return redirect(url_for("products.list_products"))
