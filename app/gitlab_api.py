import gitlab


class GitLabApi():
    url_before = 'http://172.20.18.22:10080/'
    url_after = 'http://172.20.18.22:10081/'
    token = 'F6Mzrrtoxgrpc4UfBt7o'
    target_group_names = [
        'SD-1',
        'SD-2'
    ]
    gl = None

    def __init__(self):
        self.gl = gitlab.Gitlab(
            self.url_before,
            api_version=4,
            private_token=self.token
        )

    def get_project_by_name(self, project_name):
        try:
            projects = self.get_all_projects()
            return [
                self.gl.projects.get(project.id)
                for project in projects if (
                    project.name == project_name
                    and not 'document' in project.name_with_namespace
                )
            ][0]
        except:
            pass
        return None

    def get_group_by_name(self, group_name):
        try:
            groups = self.gl.groups.list(all=True)
            return [group for group in groups if group.name == group_name][0]
        except:
            pass
        return None

    def get_group_projects(self, group_name):
        try:
            group = self.get_group_by_name(group_name)
            return group.projects.list(
                all=True,
                include_subgroups=True,
                order_by='name'
            )
        except:
            pass
        return []

    def get_all_projects(self):
        try:
            return sorted(
                [
                    project for group_name in self.target_group_names
                    for project in self.get_group_projects(group_name)
                ],
                key=lambda x: x.name
            )
        except:
            return []

    def get_all_projects_milestones_names(self):
        projects = self.get_all_projects()
        projects_versions_names = []
        for project in projects:
            milestones = self.gl.projects.get(project.id).milestones.list(
                all=True
            )
            if len(milestones) > 0:
                projects_versions_names.append(
                    {
                        'name': project.name,
                        'milestones': [
                            milestone.title for milestone in milestones
                        ]
                    }
                )
        return projects_versions_names

    def get_project_milestones(self, project_name):
        try:
            project = self.get_project_by_name(project_name)
            return project.milestones.list(all=True)
        except:
            pass
        return []

    def project_milestone_exists(self, project_name, milestone_name):
        try:
            milestones = self.get_project_milestones(project_name)
            for milestone in milestones:
                if milestone.title == milestone_name:
                    return True
        except:
            pass
        return False

    def get_project_milestone_merge_requests(
        self, project_name, milestone_name
    ):
        try:
            project = self.get_project_by_name(project_name)
            return project.mergerequests.list(
                all=True,
                milestone=milestone_name
            )
        except:
            pass
        return []

    def get_project_milestone_merge_requests_urls(
        self, project_name, milestone_name
    ):
        try:
            merge_requests = self.get_project_milestone_merge_requests(
                project_name, milestone_name
            )
            return [
                merge_request.web_url.replace(self.url_before, self.url_after)
                for merge_request in merge_requests
            ]
        except:
            pass
        return []
