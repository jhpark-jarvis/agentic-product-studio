from flask import Blueprint, flash, redirect, render_template, request, url_for

from .db import get_db
from .repositories.members import (
    create_member as create_member_record,
    delete_member as delete_member_record,
    fetch_member,
    list_members as list_member_records,
    update_member as update_member_record,
)


bp = Blueprint("members", __name__, url_prefix="/members")


def _member_form_data():
    return {
        "name": request.form.get("name", "").strip(),
        "role": request.form.get("role", "").strip(),
        "part": request.form.get("part", "").strip(),
        "contact": request.form.get("contact", "").strip(),
        "is_active": 1 if request.form.get("is_active") else 0,
    }


def _validate_member_form(data):
    errors = []
    if not data["name"]:
        errors.append("팀원 이름은 필수입니다.")
    return errors


def _fetch_member(member_id: int):
    return fetch_member(get_db(), member_id)


@bp.route("/")
def list_members():
    members = list_member_records(get_db())
    return render_template("members/list.html", members=members)


@bp.route("/new", methods=("GET", "POST"))
def create_member():
    db = get_db()
    if request.method == "POST":
        data = _member_form_data()
        errors = _validate_member_form(data)
        if not errors:
            create_member_record(db, data)
            db.commit()
            flash("팀원이 추가되었습니다.", "success")
            return redirect(url_for("members.list_members"))
        for error in errors:
            flash(error, "error")
        form_data = data
    else:
        form_data = None

    return render_template(
        "members/form.html",
        page_title="새 팀원",
        submit_label="팀원 저장",
        member=None,
        form_data=form_data,
    )


@bp.route("/<int:member_id>/edit", methods=("GET", "POST"))
def edit_member(member_id: int):
    db = get_db()
    member = _fetch_member(member_id)
    if not member:
        flash("팀원을 찾을 수 없습니다.", "error")
        return redirect(url_for("members.list_members"))

    if request.method == "POST":
        data = _member_form_data()
        errors = _validate_member_form(data)
        if not errors:
            update_member_record(db, member_id, data)
            db.commit()
            flash("팀원 정보가 수정되었습니다.", "success")
            return redirect(url_for("members.list_members"))
        for error in errors:
            flash(error, "error")
        form_data = data
    else:
        form_data = None

    return render_template(
        "members/form.html",
        page_title="팀원 수정",
        submit_label="변경 저장",
        member=member,
        form_data=form_data,
    )


@bp.route("/<int:member_id>/delete", methods=("POST",))
def delete_member(member_id: int):
    db = get_db()
    delete_member_record(db, member_id)
    db.commit()
    flash("팀원이 삭제되었습니다.", "success")
    return redirect(url_for("members.list_members"))
