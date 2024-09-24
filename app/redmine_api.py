import re, datetime, urllib.request, urllib.parse
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from .http_method import get, put, post

url_head = 'http://172.20.18.22:3000/'
token = 'c5235ddb9451f3036d6ffdb294ddc1885a3c7688'
url_foot = f'&key={token}'

INVALID_ID = -1

class TrackerType(Enum):
    Process = 'プロセス'
    Func = '機能'

class DueDateManagedBy(Enum):
    Nothing = 0 # 管理しない
    Parent = 1 # 親チケットで管理
    Children = 2 # 子チケットで管理

class ProcessType(Enum):
    Funcs = '開発項目'
    Design = '設計'
    DesignReview = '設計レビュー'
    Coding = 'コーディング'
    CodeReview = 'コードレビュー'
    CheckList = 'チェックリスト作成'
    CheckListReview = 'テスト仕様レビュー'
    Test = '部内検証'
    UserManual = '取扱説明書作成'
    ServiceManual = 'サービスマニュアル作成'
    ThirdPartyTest = '品証検証'
    Drawing = '図面登録'
    VersionList = 'バージョンリスト作成'
    Intranet = 'イントラ掲載'
    StoreSoftware = 'ソフトウェア保管'

class ProcessMetaData():
    name = ''
    due_date_managed_by = DueDateManagedBy.Nothing
    required_days = 1

    def __init__(
        self, name, due_date_managed_by=DueDateManagedBy.Nothing,
        required_days=1
    ):
        self.name = name
        self.due_date_managed_by = due_date_managed_by
        self.required_days = required_days

process_meta_datas = [
    ProcessMetaData(
        name=ProcessType.Funcs.value,
        due_date_managed_by=DueDateManagedBy.Nothing
    ),
    ProcessMetaData(
        name=ProcessType.Design.value,
        due_date_managed_by=DueDateManagedBy.Children,
        required_days=7
    ),
    ProcessMetaData(
        name=ProcessType.DesignReview.value,
        due_date_managed_by=DueDateManagedBy.Parent,
        required_days=7
    ),
    ProcessMetaData(
        name=ProcessType.Coding.value,
        due_date_managed_by=DueDateManagedBy.Children,
        required_days=7
    ),
    ProcessMetaData(
        name=ProcessType.CodeReview.value,
        due_date_managed_by=DueDateManagedBy.Parent, 
        required_days=7
    ),
    ProcessMetaData(
        name=ProcessType.CheckList.value,
        due_date_managed_by=DueDateManagedBy.Children,
        required_days=7
    ),
    ProcessMetaData(
        name=ProcessType.CheckListReview.value,
        due_date_managed_by=DueDateManagedBy.Parent,
        required_days=7
        ),
    ProcessMetaData(
        name=ProcessType.Test.value,
        due_date_managed_by=DueDateManagedBy.Children,
        required_days=7
    ),
    ProcessMetaData(
        name=ProcessType.UserManual.value,
        due_date_managed_by=DueDateManagedBy.Parent,
        required_days=7
    ),
    ProcessMetaData(
        name=ProcessType.ServiceManual.value,
        due_date_managed_by=DueDateManagedBy.Parent,
        required_days=7
    ),
    ProcessMetaData(
        name=ProcessType.ThirdPartyTest.value,
        due_date_managed_by=DueDateManagedBy.Parent,
        required_days=7
    ),
    ProcessMetaData(
        name=ProcessType.Drawing.value,
        due_date_managed_by=DueDateManagedBy.Parent
    ),
    ProcessMetaData(
        name=ProcessType.VersionList.value,
        due_date_managed_by=DueDateManagedBy.Parent
    ),
    ProcessMetaData(
        name=ProcessType.Intranet.value,
        due_date_managed_by=DueDateManagedBy.Parent
    ),
    ProcessMetaData(
        name=ProcessType.StoreSoftware.value,
        due_date_managed_by=DueDateManagedBy.Parent
    )
]

def get_process_meta_datas():
    return process_meta_datas

def get_issue_process_meta_datas():
    return [
        process_meta_data for process_meta_data in get_process_meta_datas()
        if process_meta_data.due_date_managed_by == DueDateManagedBy.Children
    ]

def get_top_url():
    return url_head

def get_users():
    url = f'{url_head}users.json?limit=100{url_foot}'
    return get(url)

def get_user_id(login_id):
    """
    >>> get_user_id('13173')
    66
    """
    try:
        users = get_users()
        for user in users['users']:
            if user['login'] == login_id:
                return user['id']
    except:
        pass
    return INVALID_ID

def user_exists(login_id):
    """
    >>> user_exists('13173')
    True
    >>> user_exists('13174')
    False
    """
    return get_user_id(login_id) != INVALID_ID

def get_projects():
    url = f'{url_head}projects.json?limit=100{url_foot}'
    return get(url)

def list_projects():
    try:
        projects = get_projects()
        return sorted(
            [project['name'] for project in projects['projects']
                if re.match('^[a-zA-Z].*', project['name'])]
        )
    except:
        return []

def get_project_id(project_name):
    """
    >>> get_project_id('FX1RMCU')
    69
    """
    try:
        projects = get_projects()
        for project in projects['projects']:
            if project['name'] == project_name:
                return project['id']
    except:
        pass
    return INVALID_ID

def get_project(project_id):
    url = f'{url_head}projects/{project_id}.json?{url_foot}'
    return get(url)

def get_project_versions(project_id):
    url = f'{url_head}projects/{project_id}/versions.json?{url_foot}'
    return get(url)

def list_projects_versions_url_in_progress():
    try:
        futures = []
        thread_pool = ThreadPoolExecutor(max_workers=4)
        projects = list_projects_versions_in_progress()
        for project in projects:
            list = []
            for version in project['versions']:
                list.append(
                    thread_pool.submit(
                        get_project_version_url,
                        project['name'],
                        version
                    )
                )
            futures.append(list)
        thread_pool.shutdown()
        return [
            {
                'name': project['name'],
                'versions': [
                    {
                        'name': project['versions'][j],
                        'redmine_url': futures[i][j].result()
                    }
                    for j in range(len(futures[i]))
                ]
            }
            for i, project in enumerate(projects)
        ]
    except:
        return []

def list_projects_versions_in_progress():
    try:
        futures = []
        thread_pool = ThreadPoolExecutor(max_workers=4)
        projects = list_projects()
        for project in projects:
            futures.append(
                thread_pool.submit(list_project_versions_in_progress, project)
            )
        thread_pool.shutdown()
        return [
            {
                'name': project,
                'versions': futures[i].result()
            }
            for i, project in enumerate(projects)
            if len(futures[i].result()) > 0
        ]
    except:
        return []

def list_project_versions_in_progress(project_name):
    try:
        project_id = get_project_id(project_name)
        versions = get_project_versions(project_id)
        return sorted(
            [
                version['name'] for version in versions['versions']
                if version['status'] == 'open'
            ],
            reverse=True
        )
    except:
        return []

def list_project_versions(project_name):
    try:
        project_id = get_project_id(project_name)
        versions = get_project_versions(project_id)
        return sorted(
            [version['name'] for version in versions['versions']],
            reverse=True
        )
    except:
        return []

def get_project_version_id(project_id, version_name):
    """
    >>> get_project_version_id(get_project_id('FX1RMCU'), 'Ver3.10')
    346
    """
    try:
        versions = get_project_versions(project_id)
        for version in versions['versions']:
            if version['name'] == version_name:
                return version['id']
    except:
        pass
    return INVALID_ID

def get_project_version_url(project_name, version_name):
    """
    >>> get_project_version_url('FX1RMCU', 'Ver3.10')
    'http://172.20.18.22:3000/versions/346/'
    >>> get_project_version_url('FX1RMCU', 'Ver3.00')
    'http://172.20.18.22:3000/versions/318/'
    """
    try:
        project_id = get_project_id(project_name)
        version_id = get_project_version_id(project_id, version_name)
        if version_id == INVALID_ID:
            raise Exception
        return get_version_url(version_id)
    except:
        return ''

def get_version_url(version_id):
    return f'{url_head}versions/{version_id}/'

def get_version(version_id):
    url = f'{url_head}versions/{version_id}.json?{url_foot}'
    return get(url)

def project_version_exists(project_name, version_name):
    """
    >>> project_version_exists('FX1RMCU', 'Ver3.10')
    True
    >>> project_version_exists('FX1RMCU', 'Ver2.50')
    False
    """
    try:
        versions = list_project_versions(project_name)
        if version_name in versions:
            return True
    except:
        pass
    return False

def create_project_version(project_id, version_digit):
    try:
        version = {
            'version': {
                'name': f'Ver{version_digit}',
            },
        }
        url = f'{url_head}projects/{project_id}/versions.json?{url_foot}'
        response = post(url, version)
        return response['version']['id']
    except:
        return INVALID_ID

def get_trackers():
    url = f'{url_head}trackers.json?{url_foot}'
    return get(url)

def get_tracker_id_by_name(tracker_name):
    """
    >>> get_tracker_id_by_name('プロセス')
    13
    >>> get_tracker_id_by_name('機能')
    2
    """
    try:
        trackers = get_trackers()
        for tracker in trackers['trackers']:
            if tracker['name'] == tracker_name:
                return tracker['id']
    except:
        pass
    return INVALID_ID

def get_tracker_id(tracker_type):
    """
    >>> get_tracker_id(TrackerType.Process)
    13
    >>> get_tracker_id(TrackerType.Func)
    2
    """
    try:
        return get_tracker_id_by_name(tracker_type.value)
    except:
        return INVALID_ID

def get_project_version_progress_tickets(project_id, version_id):
    params = {
        'project_id': project_id,
        'status_id': '*',
        'fixed_version_id': version_id,
        'limit': 100,
    }
    url = f'{url_head}issues.json?{urllib.parse.urlencode(params)}{url_foot}'
    return get(url)

def get_ticket_url(ticket_id):
    return f'{url_head}issues/{ticket_id}/'

def get_children_ticket_urls(parent_ticket_id):
    return [
        get_ticket_url(ticket_id) for ticket_id
        in get_children_ticket_ids(parent_ticket_id)
    ]

def get_ticket(ticket_id):
    url = f'{url_head}issues/{ticket_id}.json?{url_foot}'
    return get(url)

def get_children_tickets(parent_ticket_id):
    params = {
        'parent_id': parent_ticket_id,
        'status_id': '*',
        'limit': 100,
    }
    url = f'{url_head}issues.json?{urllib.parse.urlencode(params)}{url_foot}'
    return get(url)

def get_ticket_id(project_id, version_id, subject):
    """
    >>> get_ticket_id(get_project_id('FX1RMCU'), get_project_version_id(get_project_id('FX1RMCU'), 'Ver3.10'), '開発項目')
    10293
    """
    try:
        tickets = get_project_version_progress_tickets(
            project_id, version_id
        )
        for ticket in tickets['issues']:
            if ticket['subject'] == subject:
                return ticket['id']
    except:
        pass
    return INVALID_ID

def get_children_ticket_ids(parent_ticket_id):
    try:
        children_tickets = get_children_tickets(parent_ticket_id)
        return [ticket['id'] for ticket in children_tickets['issues']]
    except:
        return []

def get_root_ticket_id(project_name, version_name):
    """
    >>> get_root_ticket_id('FX1RMCU', 'Ver3.10')
    10292
    """
    try:
        # プロジェクトID取得
        project_id = get_project_id(project_name)

        # バージョンID取得
        version_id = get_project_version_id(project_id, version_name)

        return get_ticket_id(
            project_id,
            version_id,
            f'{project_name} {version_name}'
        )
    except:
        pass
    return INVALID_ID

def get_ticket_subject(ticket_id):
    """
    >>> get_ticket_subject(10208)
    '電動扉なしのレイアウト対応'
    """
    try:
        ticket = get_ticket(ticket_id)
        return ticket['issue']['subject']
    except:
        return ''

def create_ticket(
    project_id, tracker_id, subject, version_id, user_id,
    parent_ticket_id=INVALID_ID, start_date=None, due_date=None
):
    try:
        issue = {
            'issue': {
                'project_id': project_id,
                'tracker_id': tracker_id,
                'subject': subject,
                'fixed_version_id': version_id,
                'assigned_to_id': user_id,
            }
        }
        if parent_ticket_id != INVALID_ID:
            issue['issue']['parent_issue_id'] = parent_ticket_id
        if start_date is not None and due_date is not None:
            issue['issue']['start_date'] = start_date.strftime('%Y-%m-%d')
            issue['issue']['due_date'] = due_date.strftime('%Y-%m-%d')
        url = f'{url_head}issues.json?{url_foot}'
        response = post(url, issue)
        return response['issue']['id']
    except:
        return INVALID_ID

def set_parent_ticket(ticket_id, parent_id):
    issue = {
        'issue': {
            'parent_issue_id': parent_id,
        }
    }
    url = f'{url_head}issues/{ticket_id}.json?{url_foot}'
    if put(url, issue) is None:
        raise Exception

def get_relations(ticket_id):
    url = f'{url_head}issues/{ticket_id}/relations.json?{url_foot}'
    return get(url)

def create_relation(ticket_id, ticket_to_id):
    try:
        relation = {
            'relation': {
                'issue_id': ticket_id,
                'issue_to_id': ticket_to_id,
            }
        }
        url = f'{url_head}issues/{ticket_id}/relations.json?{url_foot}'
        response = post(url, relation)
        return response['relation']['id']
    except:
        return INVALID_ID

def create_process_tickets_of_root(
    project_id, version_id, user_id, parent_ticket_id, processes
):
    for process in processes:
        due_date = process.get('due_date')
        start_date = due_date - datetime.timedelta(
            days=[process_meta_data 
                for process_meta_data in get_process_meta_datas()
                if process_meta_data.name == process.get('name')
            ][0].required_days-1
        ) if due_date is not None else None
        ticket_id = create_ticket(
            project_id,
            get_tracker_id(TrackerType.Process),
            process.get('name'),
            version_id,
            user_id,
            parent_ticket_id,
            start_date,
            due_date,
        )
        if ticket_id == INVALID_ID:
            return False
    return True

def create_and_relate_process_tickets_of_func(
    project_id, version_id, user_id, func_ticket_id, processes
):
    try:
        for process in processes:
            process_name = process.get('name')
            subject = f'{get_ticket_subject(func_ticket_id)}_{process_name}'

            # プロセスチケット取得
            process_ticket_id = get_ticket_id(
                project_id, version_id, process_name
            )
            # プロセスチケットが存在しない場合はパス
            if process_ticket_id == INVALID_ID:
                continue

            ticket_id = get_ticket_id(project_id, version_id, subject)
            if ticket_id != INVALID_ID:
                # チケットが存在する
                ticket = get_ticket(ticket_id)
                parent_ticket = ticket['issue'].get('parent')
                if (
                    parent_ticket is None \
                    or parent_ticket['id'] != process_ticket_id
                ):
                    # 親チケットがプロセスチケットでない
                    # プロセスチケットを親チケットに設定
                    set_parent_ticket(ticket_id, process_ticket_id)
            else:
                # チケット作成
                due_date = process.get('due_date')
                start_date = due_date - datetime.timedelta(
                    days=[process_meta_data
                        for process_meta_data
                        in get_issue_process_meta_datas()
                        if process_meta_data.name == process.get('name')
                    ][0].required_days-1
                ) if due_date is not None else None
                ticket_id = create_ticket(
                    project_id,
                    get_tracker_id(TrackerType.Process),
                    subject,
                    version_id,
                    user_id,
                    get_ticket_id(project_id, version_id, process_name),
                    start_date,
                    due_date,
                )

            # 開発項目チケットの関連を取得
            relations = get_relations(func_ticket_id)
            if not ticket_id in [
                relation.get('issue_to_id')
                for relation in relations['relations']
            ]:
                # 関連が存在しない場合は関連付け
                relation_id = create_relation(
                    func_ticket_id,
                    ticket_id,
                )
                if relation_id == INVALID_ID:
                    raise Exception
        return True
    except:
        return False

def get_project_version_func_ticket_urls(project_name, version_name):
    try:
        # プロジェクトID取得
        project_id = get_project_id(project_name)

        # バージョンID取得
        version_id = get_project_version_id(project_id, version_name)

        # 開発項目チケット取得
        funcs_ticket_id = get_ticket_id(
            project_id, version_id, ProcessType.Funcs.value
        )

        return get_children_ticket_urls(funcs_ticket_id)
    except:
        pass
    return []

def start_develop(project_name, version_digit, login_id, processes):
    try:
        # プロジェクトID取得
        project_id = get_project_id(project_name)

        # バージョン作成
        version_id = create_project_version(project_id, version_digit)
        version = get_version(version_id)

        # ユーザID取得
        user_id = get_user_id(login_id)

        # ルートチケット作成
        root_ticket_id = create_ticket(
            project_id,
            get_tracker_id(TrackerType.Process),
            f'{project_name} {version['version']['name']}',
            version_id,
            user_id,
        )

        # 各プロセスのチケット作成
        succeed = create_process_tickets_of_root(
            project_id,
            version_id,
            user_id,
            root_ticket_id,
            processes,
        )

        if succeed:
            return get_ticket_url(root_ticket_id)
    except:
        pass
    return None

def add_issue(project_name, version_name, login_id, subject, processes):
    try:
        # プロジェクトID取得
        project_id = get_project_id(project_name)

        # バージョンID取得
        version_id = get_project_version_id(project_id, version_name)

        # ユーザID取得
        user_id = get_user_id(login_id)

        # 開発項目チケット取得
        funcs_ticket_id = get_ticket_id(
            project_id, version_id, ProcessType.Funcs.value
        )

        func_ticket_id = get_ticket_id(project_id, version_id, subject)
        if func_ticket_id != INVALID_ID:
            # 機能チケットが存在する
            func_ticket = get_ticket(func_ticket_id)
            parent_ticket = func_ticket['issue'].get('parent')
            if parent_ticket is None or parent_ticket['id'] != funcs_ticket_id:
                # 親チケットが開発項目チケットでない
                # 開発項目チケットを親チケットに設定
                set_parent_ticket(func_ticket_id, funcs_ticket_id)
        else:
            # 機能チケット作成
            func_ticket_id = create_ticket(
                project_id,
                get_tracker_id(TrackerType.Func),
                subject,
                version_id,
                user_id,
                funcs_ticket_id,
            )

        # 各プロセスのチケット作成と関連付け
        succeed = create_and_relate_process_tickets_of_func(
            project_id,
            version_id,
            user_id,
            func_ticket_id,
            processes,
        )

        if succeed:
            return get_ticket_url(func_ticket_id)
    except:
        pass
    return None

if __name__ == '__main__':
    import doctest
    doctest.testmod()
