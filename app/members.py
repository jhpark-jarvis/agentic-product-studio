from flask import Blueprint, flash, redirect, render_template, request, url_for

from .db import get_db


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
    return get_db().execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()


@bp.route("/")
def list_members():
    members = get_db().execute(
        """
        SELECT
            m.*,
            (SELECT COUNT(*) FROM wbs_tasks t WHERE t.assignee_id = m.id) AS task_count,
            (SELECT COUNT(*) FROM schedules s WHERE s.assignee_id = m.id) AS schedule_count
        FROM members m
        ORDER BY m.is_active DESC, m.name COLLATE NOCASE ASC
        """
    ).fetchall()
    return render_template("members/list.html", members=members)


@bp.route("/new", methods=("GET", "POST"))
def create_member():
    db = get_db()
    if request.method == "POST":
        data = _member_form_data()
        errors = _validate_member_form(data)
        if not errors:
            db.execute(
                """
                INSERT INTO members (name, role, part, contact, is_active)
                VALUES (?, ?, ?, ?, ?)
                """,
                (data["name"], data["role"], data["part"], data["contact"], data["is_active"]),
            )
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
            db.execute(
                """
                UPDATE members
                SET name = ?, role = ?, part = ?, contact = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (data["name"], data["role"], data["part"], data["contact"], data["is_active"], member_id),
            )
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
    db.execute("UPDATE wbs_tasks SET assignee_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE assignee_id = ?", (member_id,))
    db.execute("UPDATE schedules SET assignee_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE assignee_id = ?", (member_id,))
    db.execute("UPDATE documents SET author_id = NULL, updated_at = CURRENT_TIMESTAMP WHERE author_id = ?", (member_id,))
    db.execute("DELETE FROM members WHERE id = ?", (member_id,))
    db.commit()
    flash("팀원이 삭제되었습니다.", "success")
    return redirect(url_for("members.list_members"))
