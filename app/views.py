"""
Definition of views.
"""

import setuptools, urllib.parse, uuid, zipfile, logging, uuid
from pathlib import Path
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from wsgiref.util import FileWrapper
from django.http import StreamingHttpResponse
from bootstrap_modal_forms.generic import BSModalFormView
from .forms import (
    StartDevelopmentForm, AddIssueForm, ExportChecklistForm,
    ExportCodeReviewResultForm
)
from .gitlab_api import GitLabApi
from .redmine_api import (
    get_process_meta_datas, get_issue_process_meta_datas, get_top_url,
    start_develop, add_issue, list_projects_versions_in_progress,
    list_projects_versions_url_in_progress,
    get_project_version_func_ticket_urls, DueDateManagedBy
)
from .export_pdf import ExportPdfGitLab, ExportPdfRedmine

download_uuids = {}

def set_submit_token(request):
    submit_token = str(uuid.uuid4())
    request.session['submit_token'] = submit_token
    return submit_token

def submit_token_exists(request):
    token_in_request = request.POST.get('submit_token')
    token_in_session = request.session.pop('submit_token', '')
    if (not token_in_request) or (not token_in_session):
        return False
    return token_in_request == token_in_session

def index(request, redmine_url=get_top_url(), download_uuid=None):
    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
            'redmine_url': redmine_url,
            'download_uuid': download_uuid
        }
    )

def link(request, redmine_url):
    return index(request, redmine_url=urllib.parse.unquote(redmine_url))

def download(request, download_uuid):
    return index(request, download_uuid=download_uuid)

def download_file(request, download_uuid):
    try:
        logger = logging.getLogger(__name__)
        download_url = download_uuids.pop(download_uuid)
        download_url_path = Path(download_url)
        logger.info(f'download_url_path: {download_url_path}')
        zip_file_path = download_url_path.parent / Path('data.zip')
        with zipfile.ZipFile(
            zip_file_path, 'w',
            compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as zip_file:
            files = [
                file for file in Path(download_url_path).iterdir()
                if file.is_file()
            ]
            for file in files:
                zip_file.write(file, arcname=file.name)
        response = StreamingHttpResponse(
            FileWrapper(open(zip_file_path, 'rb'), 8 * (1024 ** 2)),
            content_type='application/zip'
        )
        return response
    except:
        return StreamingHttpResponse()

def list_developments(request):
    context = {}
    context['projects'] = []
    for project in list_projects_versions_url_in_progress():
        for version in project['versions']:
            context['projects'].append(
                {
                    'name': project['name'],
                    'version': version['name'],
                    'redmine_url': version['redmine_url']
                }
            )
    return render(request, 'app/list_developments.html', context)

class CreateTicketView(BSModalFormView):
    redmine_url = None

    def post(self, request, *args, **kwargs):
        if not submit_token_exists(request):
            return redirect(self.get_success_url())
        return super().post(self, request, *args, **kwargs)

    def get_success_url(self):
        if self.__class__.redmine_url is None:
            messages.error(self.get_form().request, "チケットの作成に失敗しました。")
            return reverse_lazy('index')
        else:
            messages.success(self.get_form().request, "チケットが作成されました。")
            return reverse_lazy('link', args=[
                urllib.parse.quote(self.__class__.redmine_url, safe='')
            ])

class StartDevelopmentView(CreateTicketView):
    template_name = 'app/start_development.html'
    form_class = StartDevelopmentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['processes'] = [
            {
                'name': process_meta_data.name,
                'has_due_date':
                    process_meta_data.due_date_managed_by == \
                        DueDateManagedBy.Parent
            } for process_meta_data in get_process_meta_datas()
        ]
        context['submit_token'] = set_submit_token(self.request)
        return context

    def form_valid(self, form):
        url = start_develop(
            form.cleaned_data.get('software'),
            form.cleaned_data.get('version'),
            form.cleaned_data.get('user'),
            [
                {
                    'name': process_meta_data.name,
                    'due_date': form.cleaned_data.get(f'due_date_{i + 1}')
                }
                for i, process_meta_data in enumerate(
                    get_process_meta_datas()
                )
                if setuptools.distutils.util.strtobool(
                    form.cleaned_data.get(f'todo_{i + 1}')
                )
            ]
        )
        self.__class__.redmine_url = url
        return super().form_valid(form)

class AddIssueView(CreateTicketView):
    template_name = 'app/add_issue.html'
    form_class = AddIssueForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['processes'] = [
            {
                'name': process_meta_data.name,
                'has_due_date': True
            } for process_meta_data in get_issue_process_meta_datas()
        ]
        context['versions'] = {}
        for project in list_projects_versions_in_progress():
            # TODO: プロセスチケットが存在するかどうかの情報を渡し、プロセスチケットが存在しないプロセスは実行なし固定とする
            context['versions'][project['name']] = project['versions']
        context['submit_token'] = set_submit_token(self.request)
        return context

    def form_valid(self, form):
        url = add_issue(
            form.cleaned_data.get('software'),
            form.cleaned_data.get('version'),
            form.cleaned_data.get('user'),
            form.cleaned_data.get('issue'),
            [
                {
                    'name': process_meta_data.name,
                    'due_date': form.cleaned_data.get(f'due_date_{i + 1}')
                }
                for i, process_meta_data in enumerate(
                    get_issue_process_meta_datas()
                )
                if setuptools.distutils.util.strtobool(
                    form.cleaned_data.get(f'todo_{i + 1}')
                )
            ]
        )
        self.__class__.redmine_url = url
        return super().form_valid(form)

class ExportPdfView(BSModalFormView):
    download_uuid = None

    def get_context_versions(self):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['versions'] = self.get_context_versions()
        context['submit_token'] = set_submit_token(self.request)
        return context

    def post(self, request, *args, **kwargs):
        if not submit_token_exists(request):
            return redirect(self.get_success_url())
        return super().post(self, request, *args, **kwargs)

    def get_export_object(self):
        raise NotImplementedError

    def get_export_urls(self, form):
        raise NotImplementedError

    def form_valid(self, form):
        export_object = self.get_export_object()
        export_urls = self.get_export_urls(form)
        url = export_object.run(export_urls)
        if url is not None:
            new_uuid = str(uuid.uuid4())
            download_uuids[new_uuid] = url
            self.__class__.download_uuid = new_uuid
        return super().form_valid(form)

    def get_success_url(self):
        if self.__class__.download_uuid is None:
            messages.error(self.get_form().request, "PDFファイルの出力に失敗しました。")
            return reverse_lazy('index')
        else:
            messages.success(self.get_form().request, "PDFファイルが出力されました。")
            return reverse_lazy('download', args=[self.__class__.download_uuid])


class ExportChecklistView(ExportPdfView):
    template_name = 'app/export_checklist.html'
    form_class = ExportChecklistForm

    def get_context_versions(self):
        versions = {}
        for project in list_projects_versions_in_progress():
            versions[project['name']] = project['versions']
        return versions

    def get_export_object(self):
        return ExportPdfRedmine()

    def get_export_urls(self, form):
        logger = logging.getLogger(__name__)
        software = form.cleaned_data.get('software')
        version = form.cleaned_data.get('version')
        logger.info(f'software: {software}, version: {version}')
        return get_project_version_func_ticket_urls(software, version)


class ExportCodeReviewResultView(ExportPdfView):
    template_name = 'app/export_codereview_result.html'
    form_class = ExportCodeReviewResultForm

    def get_context_versions(self):
        versions = {}
        gitlab_api = GitLabApi()
        for project in gitlab_api.get_all_projects_milestones_names():
            versions[project['name']] = project['milestones']
        return versions

    def get_export_object(self):
        return ExportPdfGitLab()

    def get_export_urls(self, form):
        logger = logging.getLogger(__name__)
        software = form.cleaned_data.get('software')
        version = form.cleaned_data.get('version')
        logger.info(f'software: {software}, version: {version}')
        gitlab_api = GitLabApi()
        return gitlab_api.get_project_milestone_merge_requests_urls(
            software, version
        )
