# -*- coding: utf-8 -*-
{
    'name': "Project Issue Jira",
    'version': '0.1',
    'summary': """Jira Issue Connector""",
    'description': """Allows to forward Odoo issues to Jira""",
    'author': "Cirrus",
    'website': "http://www.cirrus.pl",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    # any module necessary for this one to work correctly
    'depends': ['project'],
    'data': [
	'project_issue_jira.xml',
	'jira_config_view.xml',
    ],
    'demo': [],
    'installable': True,
}