from .decorators import require_permission
from .forms import UserSearchForm
from .models import Permission
from flask import Blueprint, current_app, render_template, request
from modules.account.models import Account

security = Blueprint("security", __name__, template_folder="templates", url_prefix="/security")

@security.route("/")
@require_permission("security", "access")
def security_index():
    modules = sorted(list(current_app.blueprints.keys()))
    return render_template("security/index.html", modules=modules)

@security.route("/query/permissions/all/")
@require_permission("security", "access")
def all_permissions():
    permissions = Permission.select(Permission, Account).join(Account)
    return render_template("security/permissions.html", header="All permissions", permissions=permissions)

@security.route("/query/permissions/module/<module>/")
@require_permission("security", "access")
def permissions_for_module(module):
    permissions = Permission.select(Permission, Account).where(Permission.module == module).join(Account)
    return render_template("security/permissions.html", header="Permissions for module: {}".format(module), permissions=permissions)

@security.route("/query/user/", methods=["GET", "POST"])
@require_permission("security", "access")
def find_user():
    form = UserSearchForm(request.form)

    if not form.validate_on_submit():
        return render_template("security/find_user.html", form=form)

    query = Account.select().where(
            (Account.first_name ** "%{}%".format(form.search.data))
          | (Account.last_name ** "%{}%".format(form.search.data))
          | (Account.email == form.search.data)
    )
    return render_template("security/users.html", results=query)

@security.route("/query/user/<int:uid>/")
def show_user(uid):
    account = Account.get(id=uid)
    return render_template("security/user.html", account=account)
