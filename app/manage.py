# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import url_for, flash, request, render_template, redirect
from flask import Blueprint, Markup, request, session
from flask_login import current_user, login_required
from sqlalchemy.sql import and_
import app.forms as forms
import app.data as data
from app.database import db
from app.ex_functions import get_lang

manage_app = Blueprint('manage_app', __name__)


@manage_app.route('/manage')
@login_required
def manage():
    ofc = data.Operators.query.filter_by(id=current_user.id).first()
    if current_user.role_id == 3 and ofc is None:
        flash(get_lang(17),
              "danger")
        return redirect(url_for('core.root'))
    if ofc is None:
        ofc = 0
    else:
        ofc = ofc.id
    return render_template("manage.html",
                           ptitle="Management",
                           navbar="#snb1",
                           ooid=ofc,
                           serial=data.Serial.query,
                           offices=data.Office.query,
                           operators=data.Operators.query,
                           tasks=data.Task.query)


@manage_app.route('/all_offices')
@login_required
def all_offices():
    if current_user.role_id == 3:
        flash(get_lang(17),
              "danger")
        return redirect(url_for('core.root'))
    page = request.args.get('page', 1, type=int)
    if page > int(data.Serial.query.count() / 10) + 1:
        flash(get_lang(4),
              'danger')
        return redirect(url_for('manage_app.all_offices'))
    pagination = data.Serial.query.order_by(
        data.Serial.p, data.Serial.timestamp.desc
        ()).paginate(page, per_page=10, error_out=False)
    return render_template('all_offices.html',
                           officesp=pagination.items,
                           pagination=pagination,
                           len=len,
                           ptitle="All Offices",
                           serial=data.Serial.query,
                           offices=data.Office.query,
                           tasks=data.Task.query,
                           users=data.User.query,
                           operators=data.Operators.query,
                           navbar="#snb1",
                           hash="#da2")


@manage_app.route('/offices/<int:o_id>', methods=['GET', 'POST'])
@login_required
def offices(o_id):
    ofc = data.Office.query.filter_by(id=o_id).first()
    if ofc is None:
        flash(
            get_lang(4),
            "danger"
        )
        return redirect(url_for("manage_app.all_offices"))
    if current_user.role_id == 3 and data.Operators.query.filter_by(id=current_user.id).first() is None:
        flash(
            get_lang(17),
            "danger"
        )
        return redirect(url_for('core.root'))
    form = forms.Offices_a(upd=ofc.prefix, defLang=session.get('lang'))
    page = request.args.get('page', 1, type=int)
    if page > int(data.Serial.query.filter_by(office_id=o_id).count() / 10) + 1:
        flash(
            get_lang(4),
            'danger'
        )
        return redirect(url_for('manage_app.offices', o_id=o_id))
    pagination = data.Serial.query.filter_by(
        office_id=o_id
    ).order_by(
        data.Serial.p
    ).order_by(
        data.Serial.number.desc()
    ).paginate(
        page,
        per_page=10,
        error_out=False
    )
    if form.validate_on_submit():
        mka = data.Office.query.filter_by(name=form.name.data)
        for f in mka:
            if f.id != o_id:
                flash(get_lang(42),
                      "danger")
                return redirect(url_for("manage_app.offices", o_id=o_id))
        ofc.name = form.name.data
        ofc.prefix = form.prefix.data.upper()
        db.session.commit()
        flash(get_lang(44),
              "info")
        return redirect(url_for('manage_app.offices', o_id=o_id))
    form.name.data = ofc.name
    form.prefix.data = ofc.prefix.upper()
    print()
    return render_template('offices.html',
                           form=form,
                           officesp=pagination.items,
                           pagination=pagination,
                           ptitle="Office : " + ofc.prefix + str(ofc.name),
                           o_id=o_id,
                           ooid=ofc,
                           len=len,
                           serial=data.Serial.query,
                           offices=data.Office.query,
                           tasks=data.Task.query,
                           users=data.User.query,
                           operators=data.Operators.query,
                           navbar="#snb1",
                           dropdown="#dropdown-lvl" + str(o_id),
                           hash="#t1" + str(o_id))


@manage_app.route('/office_a', methods=['GET', 'POST'])
@login_required
def office_a():
    if current_user.role_id == 3:
        flash(get_lang(17),
              "danger")
        return redirect(url_for('core.root'))
    form = forms.Offices_a(defLang=session.get('lang'))
    if form.validate_on_submit():
        if data.Office.query.filter_by(name=form.name.
                                       data).first() is not None:
            flash(get_lang(42),
                  "danger")
            return redirect(url_for("manage_app.all_offices"))
        db.session.add(data.Office(form.name.data,
                                   form.prefix.data.upper()))
        db.session.commit()
        flash(get_lang(45),
              "info")
        return redirect(url_for("manage_app.all_offices"))
    return render_template("office_add.html",
                           form=form,
                           ptitle="Adding new office",
                           offices=data.Office.query,
                           tasks=data.Task.query,
                           operators=data.Operators.query,
                           navbar="#snb1",
                           hash="#da3",
                           serial=data.Serial.query)


@manage_app.route('/office_d/<int:o_id>')
@login_required
def office_d(o_id):
    if current_user.role_id == 3:
        flash(get_lan(17),
              "danger")
        return redirect(url_for('core.root'))
    if data.Office.query.filter_by(id=o_id).first() is None:
        flash(get_lang(4),
              "danger")
        return redirect(url_for("manage_app.offices", o_id=o_id))
    if data.Serial.query.filter(and_(data.Serial.office_id == o_id,
                                        data.Serial.number != 100)
                                   ).count() > 0:
        flash(get_lang(46),
              "danger")
        return redirect(url_for("manage_app.offices", o_id=o_id))
    for t in data.Task.query.filter_by(office_id=o_id):
        if t is not None:
            db.session.delete(t)
    db.session.delete(data.Office.query.filter_by(id=o_id).first())
    db.session.commit()
    flash(get_lang(47),
          "info")
    return redirect(url_for("manage_app.all_offices"))


@manage_app.route('/office_da')
@login_required
def office_da():
    if current_user.role_id == 3:
        flash(get_lang(17),
              "danger")
        return redirect(url_for('core.root'))
    if data.Office.query.count() <= 0:
        flash(get_lang(53),
              "danger")
        return redirect(url_for("manage_app.all_offices"))
    if data.Serial.query.count() > data.Office.query.count():
        flash(get_lang(46),
              "danger")
        return redirect(url_for("manage_app.all_offices"))
    for s in data.Serial.query:
        db.session.delete(s)
    for f in data.Office.query:
        for t in data.Task.query.filter_by(office_id=f.id):
            db.session.delete(t)
        db.session.delete(f)
    db.session.commit()
    flash(get_lang(47),
          "info")
    return redirect(url_for("manage_app.all_offices"))


pll = []


@manage_app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if current_user.role_id == 3:
        flash(get_lang(17),
              "danger")
        return redirect(url_for('core.root'))
    form = forms.Search_s(session.get('lang'))
    if form.validate_on_submit() or request.args.get("page"):
        from sqlalchemy.sql import and_
        terms = []
        counter = 0
        global pll
        if request.args.get("page"):
            ll = pll
        else:
            ll = [form.number.data, form.date.data, form.tl.data]
            pll = ll
        for l in ll:
            counter += 1
            if l is not None:
                if counter == 1:
                    if len(str(l)) >= 2:
                        terms.append("number=" + str(ll[0]))
                elif counter == 2:
                    if len(str(l)) >= 2:
                        terms.append(
                            "date='" + ll[1].strftime('%Y-%m-%d') + "'")
                elif counter == 3:
                    if l != 0:
                        terms.append("office_id=" + str(ll[2]))
        if len(terms) == 0:
            flash(get_lang(48),
                  "danger")
            return redirect(url_for("manage_app.search"))
        serials = data.Serial.query.filter(and_(*terms))
        if serials.first() is None or serials.order_by(data.Serial.id.desc()).first() == 100:
            flash(get_lang(49), "info")
            return redirect(url_for("manage_app.search"))
        page = request.args.get('page', 1, type=int)
        if page > int(data.Serial.query.filter(and_(*terms)).count() / 10) + 1:
            flash(get_lang(4),
                  'danger')
            return redirect(url_for('manage_app.search'))
        pagination = data.Serial.query.filter(
            and_(*terms)).order_by(data.Serial
                                   .timestamp
                                   .desc()).paginate(
                                       page,
                                       per_page=10,
                                       error_out=False)
        return render_template("search_r.html",
                               serials=serials,
                               ptitle="Tickets search",
                               offices=data.Office.query,
                               tasks=data.Task.query,
                               users=data.User.query,
                               pagination=pagination,
                               serialsp=pagination.items,
                               operators=data.Operators.query,
                               len=len,
                               navbar="#snb1",
                               hash="#da1",
                               serial=data.Serial.query)
    return render_template("search.html",
                           form=form,
                           ptitle="Tickets search",
                           offices=data.Office.query,
                           tasks=data.Task.query,
                           operators=data.Operators.query,
                           navbar="#snb1",
                           hash="#da1",
                           serial=data.Serial.query)


@manage_app.route('/task/<int:o_id>', methods=['POST', 'GET'])
@login_required
def task(o_id):
    form = forms.Task_a(session.get('lang'))
    task = data.Task.query.filter_by(id=o_id).first()
    if task is None:
        # Check if ths task exists
        flash(
            get_lang(4),
            "danger"
        )
        return redirect(url_for("core.root"))
    if current_user.role_id == 3 and data.Operators.query.filter_by(id=current_user.id).first() is None:
        # Operator does not have right
        flash(
            get_lang(17),
            "danger"
        )
        return redirect(url_for('core.root'))
    if current_user.role_id == 3 and task.office_id != data.Operators.query.filter_by(id=current_user.id).first().office_id:
        # Operator does not have access to the office
        flash(
            get_lang(17),
            "danger"
        )
        return redirect(url_for('core.root'))
    ofc = data.Office.query.filter_by(id=task.office_id).first()
    page = request.args.get('page', 1, type=int)
    if page > int(data.Serial.query.filter_by(task_id=o_id).count() / 10) + 1:
        flash(get_lang(4),
              'danger')
        return redirect(url_for('manage_app.task', o_id=o_id))
    pagination = data.Serial.query.filter_by(
        task_id=o_id).order_by(data.Serial
                               .timestamp
                               .desc()).paginate(
                                   page, per_page=10,
                                   error_out=False)
    if form.validate_on_submit():
        mka = data.Task.query.filter_by(name=form.name.data)
        for f in mka:
            if f.id != o_id:
                flash(get_lang(43),
                      "danger")
                return redirect(url_for("manage_app.task", o_id=o_id))
        task.name = form.name.data
        db.session.add(task)
        db.session.commit()
        flash(get_lang(50),
              "info")
        return redirect(url_for("manage_app.task", o_id=o_id))
    if not form.errors:
        form.name.data = task.name
    return render_template('tasks.html',
                           form=form,
                           ptitle="Task : " + task.name,
                           tasksp=pagination.items,
                           pagination=pagination,
                           serial=data.Serial.query,
                           o_id=o_id,
                           len=len,
                           offices=data.Office.query,
                           tasks=data.Task.query,
                           users=data.User.query,
                           operators=data.Operators.query,
                           task=task,
                           navbar="#snb1",
                           dropdown="#dropdown-lvl" + str(task.office_id),
                           hash="#tt" + str(task.office_id) + str(o_id))


@manage_app.route('/task_d/<int:t_id>')
@login_required
def task_d(t_id):
    task = data.Task.query.filter_by(id=t_id).first()
    if task is None:
        flash(get_lang(4),
              "danger")
        return redirect(url_for("core.root"))
    if current_user.role_id == 3 and oid is data.Operators.query.filter_by(id=current_user.id).first():
        flash(get_lang(17),
              "danger")
        return redirect(url_for('core.root'))
    if current_user.role_id == 3 and task.office_id != data.Operators.query.filter_by(id=current_user.id).first().office_id:
        flash(get_lang(17),
              "danger")
        return redirect(url_for('core.root'))
    if data.Serial.query.filter(and_(data.Serial.task_id == t_id,
                                     data.Serial.number != 100)).count() > 0:
        flash(get_lang(46),
              "danger")
        return redirect(url_for("manage_app.task", o_id=t_id))
    evil = data.Serial.query.filter_by(task_id=t_id, number=100).first()
    if evil is not None:
        db.session.delete(evil)
    db.session.delete(data.Task.query.filter_by(id=t_id).first())
    db.session.commit()
    flash(get_lang(51),
          "info")
    return redirect(url_for("manage_app.offices", o_id=task.office_id))


@manage_app.route('/task_a/<int:o_id>', methods=['GET', 'POST'])
@login_required
def task_a(o_id):
    form = forms.Task_a(session.get('lang'))
    if data.Office.query.filter_by(id=o_id).first() is None:
        flash(get_lang(4),
              "danger")
        return redirect(url_for("core.root"))
    if current_user.role_id == 3 and data.Operators.query.filter_by(id=current_user.id).first() is None:
        flash(get_lang(17),
              "danger")
        return redirect(url_for('core.root'))
    if current_user.role_id == 3 and o_id != data.Operators.query.filter_by(id=current_user.id).first().office_id:
        flash(get_lang(17),
              "danger")
        return redirect(url_for('core.root'))
    if form.validate_on_submit():
        if data.Task.query.filter_by(name=form.name.data).first() is not None:
            flash(get_lang(43),
                  "danger")
            return redirect(url_for("manage_app.task_a"))
        db.session.add(data.Task(form.name.data, o_id))
        db.session.commit()
        flash(get_lang(52), "info")
        return redirect(url_for("manage_app.offices", o_id=o_id))
    return render_template("task_add.html", form=form,
                           offices=data.Office.query,
                           serial=data.Serial.query,
                           tasks=data.Task.query,
                           operators=data.Operators.query,
                           navbar="#snb1",
                           dropdown="#dropdown-lvl" + str(o_id),
                           hash="#t3" + str(o_id),
                           ptitle="Add new task")
