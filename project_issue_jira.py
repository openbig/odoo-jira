from openerp.osv import fields, osv
from jira.client import JIRA
from openerp.tools.translate import _
import logging
import openerp.exceptions
from jira_config import JIRA_SERVER, JIRA_PROTOCOL, JIRA_USERNAME, JIRA_PASSWORD, jira_configuration


class project_issue_jira(osv.osv):

  _inherit = ["project.issue"]

  ###ids from JIRA app
  _columns = {
    'jira_id': fields.integer('JIRA id', size=11, readonly=True),
    'jira_key': fields.char('JIRA key', size=256, readonly=True),
    'jira_status': fields.char('JIRA status', size=30, readonly=True),
    'jira_link': fields.char('JIRA Issue Link', size=256, readonly=True),
  }


class project_jira(osv.osv):

  _inherit = ["project.project"]


  _columns = {
    'jira_project_key': fields.char('JIRA Project Key', size=10),
  }

  ##Odoo Bugs - OB
  _defaults = {
    'jira_project_key': '',
  }


  def connect_to_jira(self, cr, uid, context=None):

    #jserver=super(jira_configuration, self).get_default_jira_server(cr, uid, ids, context=None)
    jserver=self.pool.get('ir.config_parameter').get_param(cr, uid, JIRA_SERVER)
    jprotocol=self.pool.get('ir.config_parameter').get_param(cr, uid, JIRA_PROTOCOL)
    jusername=self.pool.get('ir.config_parameter').get_param(cr, uid, JIRA_USERNAME)
    jpassword=self.pool.get('ir.config_parameter').get_param(cr, uid, JIRA_PASSWORD)

    serverlink = jprotocol+'://'+jserver

    options = {
	'server': serverlink
    }

    ###connect to jira
    jira=JIRA(options,basic_auth=(jusername, jpassword))

    return jira

  def get_jira_issue_link(self, cr, uid, isskey):
    jserver=self.pool.get('ir.config_parameter').get_param(cr, uid, JIRA_SERVER)
    jprotocol=self.pool.get('ir.config_parameter').get_param(cr, uid, JIRA_PROTOCOL)

    return jprotocol+'://'+jserver+'/browse/'+isskey

  def cron_jira_sync(self, cr, uid, context=None):
    logging.info('Sync all - cron job')
    project_ids = self.pool.get('project.project').search(cr, uid, [('jira_project_key', '<>', '""')])
    if project_ids:
	projects = self.pool.get('project.project').browse(cr, uid, project_ids, context=context)
	jira = self.connect_to_jira(cr, uid, context=None)

        for project in projects:
	    project_key_jira = self.check_if_project_exists(cr, uid, project.jira_project_key, jira)
	    jira_project_key = project.jira_project_key
	    logging.info(project_key_jira)

	    if project_key_jira == 1:
		self.sync_project(cr, uid, project.issue_ids, jira_project_key, jira, context=None)
	    else:
		logging.info('Current JIRA Project Key: ('+project.jira_project_key+') value do not exist in JIRA application! Skipping...')

    return True


  def check_if_project_exists(self, cr, uid, project_key, jira):
    ###check if project exists in jira
    projects = jira.projects()
    i=0
    for key in projects:
	key = str(key.key)
	proj = jira.project(key)
	if proj.key==project_key:
	    i=1

    if i==1:
	return 1
    else:
	return 0

  def sync_project(self, cr, uid, project_issue_ids, jira_project_key, jira, context=None):
	###get all issues from odoo - check if it was already transfered to jira.If no - transfer, if yes - check if there's anything to update.
	for issueid in project_issue_ids:
	    logging.info(issueid.id)
	    odoo_issue = self.get_project_issues(cr, uid, issueid.id, context=None)
	    name = odoo_issue.name
	    jira_id = odoo_issue.jira_id
	    jira_key = odoo_issue.jira_key
	    desc = odoo_issue.description

	    ##if jira_id and jira_key are empty it means that this is a new issue, which we need to transfer to jira
	    if not jira_id and not jira_key:
		logging.info('jira_id and jira_key are empty - creating issue in JIRA app...')
		issue_dict = {
	    	    'project': {'key': str(jira_project_key)},
	    	    'summary': str(name),
	    	    'description': str(desc),
	    	    'issuetype': {'name': 'Bug'},
		}

		new_issue = jira.create_issue(fields=issue_dict)

		##get issue id
		issid = new_issue.id
		isskey = new_issue.key
		issstatus = new_issue.fields.status.name
		#isslink = new_issue.fields.issuelinks

		isslink = self.get_jira_issue_link(cr, uid, isskey)
		logging.info(isslink)
		#logging.info(dir(isslink))

		##save values from jira to odoo issue
		issue_obj = self.pool.get('project.issue')
		issue_obj.write(cr, uid, issueid.id, {'jira_key': isskey}, context=context)
		issue_obj.write(cr, uid, issueid.id, {'jira_id': issid}, context=context)
		issue_obj.write(cr, uid, issueid.id, {'jira_status': issstatus}, context=context)
		issue_obj.write(cr, uid, issueid.id, {'jira_link': isslink}, context=context)

	    ##jira_id and jira_key are filled. Update issues...
	    else:
		logging.info('Issue exists in JIRA application. Doing update...')

		issue_to_update = jira.issue(jira_key)
		jira_status = issue_to_update.fields.status.name
		jira_description = issue_to_update.fields.description
		odoo_jira_status = odoo_issue.jira_status
		odoo_jira_description = odoo_issue.description
		
		if jira_description != odoo_jira_description:
		    ###if jira issue has no description it sends 'False' - need to eliminate this
		    if jira_description != 'False':
			###differences between descriptions. Doing update...(field+openchatter)
			issue_obj_update = self.pool.get('project.issue')
			issue_obj_update.write(cr, uid, issueid.id, {'description': jira_description}, context=context)
			issue_obj_update.message_post(cr, uid, issueid.id, body=_("JIRA issue description has changed."), context=context)


		if str(jira_status) != str(odoo_jira_status):
		    ###differencess between statuses. Doing update...(field+openchatter)
		    issue_obj_update = self.pool.get('project.issue')
		    issue_obj_update.write(cr, uid, issueid.id, {'jira_status': jira_status}, context=context)
		    issue_obj_update.message_post(cr, uid, issueid.id, body=_("JIRA issue status has changed to "+str(jira_status)), context=context)

		    task_type_id=self.get_task_id(cr, uid, jira_status, context=None)
		    logging.info(task_type_id)
		    if task_type_id:
			###update issue status
			issue_obj_update.write(cr, uid, issueid.id, {'stage_id': task_type_id}, context=context)

		logging.info(odoo_issue.name)



  def get_task_id(self, cr, uid, jira_status, context=None):
    query = str(jira_status)+"%"
    task_type = self.pool.get('project.task.type').search(cr, uid, [('name', 'like', query)])
    if task_type:
	task_type_id = self.pool.get('project.task.type').browse(cr, uid, task_type, context=context)

    return task_type_id.id


  def get_task_done_id(self, cr, uid, context=None):
    task_type = self.pool.get('project.task.type').search(cr, uid, [('name', '=', 'Done')])
    if task_type:
	task_type_id = self.pool.get('project.task.type').browse(cr, uid, task_type, context=context)

    return task_type_id.id


  def sync_jira_now(self, cr, uid, ids, context=None):

    jira = self.connect_to_jira(cr, uid, context=None)
    project = self.get_project(cr, uid, ids, context=None)
    jira_project_key = project.jira_project_key

    if jira_project_key:
	project_key_jira = self.check_if_project_exists(cr, uid, jira_project_key, jira)

	if project_key_jira == 1:
	    self.sync_project(cr, uid, project.issue_ids, jira_project_key, jira, context=None)
	else:
	    raise osv.except_osv(_('Information!'), _('Current JIRA Project Key value do not exist in JIRA application!'))
    else:
	raise osv.except_osv(_('Information!'), _('Current ODOO project is not assigned to JIRA project!'))

    return True


  def get_project_issues(self, cr, uid, ids, context=None):
    issues = self.pool.get('project.issue').browse(cr, uid, ids, context=context)
    return issues

  def get_project(self, cr, uid, ids, context=None):
    project = self.pool.get('project.project').browse(cr, uid, ids, context=context)
    return project

  def get_project_id(self, cr, uid, ids, context=None):
    issuerow = self.pool.get('project.issue').browse(cr, uid, ids, context=context)
    return issuerow.project_id.id

