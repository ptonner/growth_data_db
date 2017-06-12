from ..forms import SearchForm, ProjectForm
from ..app import machine
from popmachine import models

from sqlalchemy import not_
import flask
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user

profile = Blueprint('project', __name__)

@profile.route('/project/<projectid>')
def project(projectid):
    searchform = SearchForm()
    project = machine.session.query(models.Project).filter_by(id=projectid).one_or_none()

    if not project or (not project.published and (not current_user.is_authenticated or project.owner != current_user)):
        flask.flash('project not found or you do not have permissions to view it!')
        return redirect(url_for('index'))

    return render_template("project.html", project=project, searchform = searchform)

@profile.route('/projects/')
def projects():

    if not current_user.is_authenticated:
        myprojects = None
        projects = machine.session.query(models.Project).filter_by(published=True)
    else:
        myprojects = machine.session.query(models.Project).filter_by(owner=current_user)
        projects = machine.session.query(models.Project).filter_by(published=True).filter(not_(models.Project.owner==current_user))

    searchform = SearchForm()

    return render_template("projects.html", myprojects=myprojects, searchform=searchform, projects=projects)

@profile.route('/project/<projectid>/publish')
@login_required
def project_publish(projectid):

    project = machine.session.query(models.Project).filter_by(id=projectid, owner=current_user).one_or_none()

    if project:

        project.published = True
        machine.session.add(project)
        machine.session.commit()

        return redirect((url_for('project.project', projectid=project.id)))

    return redirect(url_for('project.projects'))

@profile.route('/project/<projectid>/unpublish')
@login_required
def project_unpublish(projectid):

    project = machine.session.query(models.Project).filter_by(id=projectid, owner=current_user).one_or_none()

    if project:

        project.published = False
        machine.session.add(project)
        machine.session.commit()

        return redirect((url_for('project.project', projectid=project.id)))

    return redirect(url_for('project.projects'))

@profile.route('/project/<projectid>/edit', methods=['GET', 'POST'])
@login_required
def project_edit(projectid):

    project = machine.session.query(models.Project).filter_by(id=projectid, owner=current_user).one_or_none()

    if project:

        searchform = SearchForm()
        form = ProjectForm()

        form.name.data = project.name
        form.description.data = project.description
        form.design.data = project.design
        form.published.data = project.published
        form.citation_pmid.data = project.citation_pmid

        if request.method=="GET":
            return render_template("project-form.html", form=form, searchform = searchform, redirect=url_for('project.project_edit', projectid=project.id))
        else:

            project.name = request.form['name']
            project.description = request.form['description']
            project.design = request.form['design']
            project.published = 'published' in request.form and request.form['published']
            project.citation = request.form['citation']
            project.citation_pmid = request.form['citation_pmid']

            machine.session.add(project)
            machine.session.commit()

    flask.flash('no project found!')
    return redirect(url_for('project.projects'))


@profile.route('/project-create/', methods=['GET', "POST"])
@login_required
def project_create():

    searchform = SearchForm()
    form = ProjectForm()

    if request.method=="GET":
        return render_template("project-create.html", form=form, searchform = searchform)
    else:

        # print request.form

        name = request.form['name']
        description = request.form['description']
        design = request.form['design']
        published = 'published' in request.form and request.form['published']
        citation = request.form['citation']
        citation_pmid = request.form['citation_pmid']

        now = datetime.datetime.now()

        project = models.Project(name=name, description=description, design=design, published=published, citation_text=citation, citation_pmid=citation_pmid, owner=current_user, submission_date=now, modified_date=now)
        machine.session.add(project)
        machine.session.commit()

        return redirect(url_for('project.project', projectid=project.id))
    return redirect(url_for('project.project_create'))
