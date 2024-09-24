"""
Definition of forms.
"""

from datetime import date
import setuptools
from django import forms
from django.utils.translation import gettext_lazy as _
from bootstrap_modal_forms.forms import BSModalForm
from .redmine_api import (
    list_projects, project_version_exists, get_process_meta_datas,
    get_issue_process_meta_datas, user_exists, DueDateManagedBy
)
from .gitlab_api import GitLabApi


TODO_TYPES = (
    (True, 'する'),
    (False, 'しない'),
)


class StartDevelopmentForm(BSModalForm):
    software = forms.ChoiceField(label='ソフトウェア')
    version = forms.CharField(label='バージョン', max_length=5)
    user = forms.CharField(label='担当者（Redmine ID）', max_length=10)
    for i, process_meta_data in enumerate(get_process_meta_datas()):
        exec(f'todo_{i + 1} = forms.ChoiceField()')
        exec(f'due_date_{i + 1} = forms.DateField()')

    class Meta:
        fields = ['software', 'version', 'user']
        for i, process_meta_data in enumerate(get_process_meta_datas()):
            fields.append(f'todo_{i + 1}')
            fields.append(f'due_date_{i + 1}')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['software'].choices = \
            tuple([(project, project) for project in list_projects()])
        for i, process_meta_data in enumerate(get_process_meta_datas()):
            self.fields[f'todo_{i + 1}'].choices = TODO_TYPES
            self.fields[f'due_date_{i + 1}'].widget = \
                forms.DateInput(attrs={'type': 'date'})
            self.fields[f'due_date_{i + 1}'].required = False
            if (process_meta_data.due_date_managed_by != \
                DueDateManagedBy.Parent
            ):
                self.fields[f'due_date_{i + 1}'].initial = None
            else:
                self.fields[f'due_date_{i + 1}'].initial = date.today()

    def clean_version(self):
        software = self.cleaned_data.get('software')
        version = self.cleaned_data.get('version')
        if project_version_exists(software, f'Ver{version}'):
            raise forms.ValidationError('既に存在します。')
        return version

    def clean_user(self):
        user = self.cleaned_data.get('user')
        if not user_exists(user):
            raise forms.ValidationError('ユーザーが存在しません。')
        return user

    def clean_due_date(self, number):
        todo = setuptools.distutils.util.strtobool(
            self.cleaned_data.get(f'todo_{number}')
        )
        due_date = self.cleaned_data.get(f'due_date_{number}')
        process_meta_data = get_process_meta_datas()[number - 1]
        if (process_meta_data.due_date_managed_by == DueDateManagedBy.Parent
            and todo
        ):
            today = date.today()
            if due_date is None:
                raise forms.ValidationError('入力が必須です。')
            elif due_date < today:
                raise forms.ValidationError('過去の日付は指定できません。')
        return due_date

    for i, process_meta_data in enumerate(get_process_meta_datas()):
        exec(
            f'def clean_due_date_{i + 1}(self):\r\n' \
            f'    return self.clean_due_date({i + 1})'
        )


class AddIssueForm(BSModalForm):
    software = forms.CharField(label='ソフトウェア', widget=forms.Select)
    version = forms.CharField(label='バージョン', widget=forms.Select)
    issue = forms.CharField(label='開発項目名', max_length=50)
    user = forms.CharField(label='担当者（Redmine ID）', max_length=10)
    for i, process_meta_data in enumerate(get_issue_process_meta_datas()):
        exec(f'todo_{i + 1} = forms.ChoiceField()')
        exec(f'due_date_{i + 1} = forms.DateField()')

    class Meta:
        fields = ['software', 'version', 'issue', 'user']
        for i, process_meta_data in enumerate(get_issue_process_meta_datas()):
            fields.append(f'todo_{i + 1}')
            fields.append(f'due_date_{i + 1}')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i, process_meta_data in enumerate(get_issue_process_meta_datas()):
            self.fields[f'todo_{i + 1}'].choices = TODO_TYPES
            self.fields[f'due_date_{i + 1}'].widget = \
                forms.DateInput(attrs={'type': 'date'})
            self.fields[f'due_date_{i + 1}'].required = False
            self.fields[f'due_date_{i + 1}'].initial = date.today()

    def clean_version(self):
        software = self.cleaned_data.get('software')
        version = self.cleaned_data.get('version')
        if not project_version_exists(software, version):
            raise forms.ValidationError('存在しないバージョンです。')
        return version

    def clean_user(self):
        user = self.cleaned_data.get('user')
        if not user_exists(user):
            raise forms.ValidationError('ユーザーが存在しません。')
        return user

    def clean_due_date(self, number):
        todo = setuptools.distutils.util.strtobool(
            self.cleaned_data.get(f'todo_{number}')
        )
        due_date = self.cleaned_data.get(f'due_date_{number}')
        if todo:
            today = date.today()
            if due_date is None:
                raise forms.ValidationError('入力が必須です。')
            elif due_date < today:
                raise forms.ValidationError('過去の日付は指定できません。')
        return due_date

    for i, process_meta_data in enumerate(get_issue_process_meta_datas()):
        exec(
            f'def clean_due_date_{i + 1}(self):\r\n' \
            f'    return self.clean_due_date({i + 1})'
        )


class ExportPdfForm(BSModalForm):
    software = forms.CharField(label='ソフトウェア', widget=forms.Select)
    version = forms.CharField(label='バージョン', widget=forms.Select)


class ExportChecklistForm(ExportPdfForm):
    def clean_version(self):
        software = self.cleaned_data.get('software')
        version = self.cleaned_data.get('version')
        if not project_version_exists(software, version):
            raise forms.ValidationError('存在しないバージョンです。')
        return version


class ExportCodeReviewResultForm(ExportPdfForm):
    def clean_version(self):
        gitlab_api = GitLabApi()
        software = self.cleaned_data.get('software')
        version = self.cleaned_data.get('version')
        if not gitlab_api.project_milestone_exists(software, version):
            raise forms.ValidationError('存在しないバージョンです。')
        return version
