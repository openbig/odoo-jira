from openerp.osv import fields, osv
from jira.client import JIRA
from openerp.tools.translate import _
import logging
import openerp.exceptions
from jira_config import JIRA_SERVER, JIRA_PROTOCOL, JIRA_USERNAME, JIRA_PASSWORD, jira_configuration
from openerp import SUPERUSER_ID
import string
import os
import re

class project_issue_jira(osv.osv):

  _inherit = ["project.issue"]

  ###ids from JIRA app
  _columns = {
    'jira_id': fields.integer('JIRA id', size=11, readonly=True),
    'jira_key': fields.char('JIRA key', size=256, readonly=True),
    'jira_status': fields.char('JIRA status', size=30, readonly=True),
    'jira_link': fields.char('JIRA Issue Link', size=256, readonly=True),
    'jira_comments': fields.char('JIRA Comments', size=256, readonly=True),
    'jira_attachments': fields.char('JIRA Attachments', size=256, readonly=True),
  }

  def get_task_id(self, cr, uid, jira_status, context=None):
    query = str(jira_status)+"%"
    task_type = self.pool.get('project.task.type').search(cr, uid, [('name', 'like', query)])
    if task_type:
	task_type_id = self.pool.get('project.task.type').browse(cr, uid, task_type, context=context)

    return task_type_id.id


  def issue_escalate(self, cr, uid, ids, context=None):        # FIXME rename this method to issue_escalate

    for issue in self.browse(cr, uid, ids, context=context):
        data = {}
        esc_proj = issue.project_id.project_escalation_id
        if not esc_proj:
            raise osv.except_osv(_('Warning!'), _('You cannot escalate this issue.\nThe relevant Project has not configured the Escalation Project!'))

        data['project_id'] = esc_proj.id
        if esc_proj.user_id:
            data['user_id'] = esc_proj.user_id.id
        issue.write(data)

        if issue.task_id:
            issue.task_id.write({'project_id': esc_proj.id, 'user_id': False})

	###After escalation the stage changes to Open
	###task_type_id=pj.get_task_id(cr, uid, "Open", context=None)
	task_type_id=self.get_task_id(cr, uid, "Open", context=None)
	issue.write({'stage_id': task_type_id})

    return True


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

	prioritymap = {
	    "0":"Minor",
	    "1":"Major",
	    "2":"Critical"
	}

	def _get_mail(issue_id):
    	    email_obj = self.pool.get('mail.message')
            email_id = email_obj.search(cr, uid, [('model', '=', 'project.issue'), ('type', '=', 'email'), ('res_id', '=', issue_id)], context=context)

	    return email_obj.browse(cr, uid, email_id, context=context)

	def _get_attachments(issue_id):
    	    attach_obj = self.pool.get('ir.attachment')
            attachment_ids = attach_obj.search(cr, uid, [('res_model', '=', 'project.issue'), ('res_id', '=', issue_id)], context=context)

	    return attach_obj.browse(cr, uid, attachment_ids, context=context)

	def _save_attachments(datas_fname,datas):
	    b64_fname = str(datas_fname)
            fout = open(b64_fname, 'wb')
            fout.write(datas.decode('base64'))
            fout.close
	    return True

	def _add_attachment(attachment,isskey):
	    att = self.pool.get('ir.attachment').browse(cr, SUPERUSER_ID, attachment.id, context=context)
	    fi='/tmp/'+att.datas_fname
	    sa = _save_attachments(fi, att.datas)

	    if sa:
		jira.add_attachment(isskey,fi,att.datas_fname)
    		if os.path.exists(fi):
            	    os.remove(fi)

	    return True


	def _handle_attachments(attachments, odoo_jira_attachments, isskey, issue_obj_update):
	    attids=''
            for attachment in attachments:
		attids = str(attachment.id)+";"+attids

            if attids:
                attids=attids[:-1]

            if odoo_jira_attachments:
                logging.info('Attachment exists. Check and add only the new one!')

                if odoo_jira_attachments != attids:
                    logging.info('Attachments are NOT equals')
                    attidtab=string.split(odoo_jira_attachments, ';')

                    ###checking if attachment id is already saved in database
                    for attachment in attachments:
                        cexists=0
                        for idtab in attidtab:
                            if str(attachment.id)==str(idtab):
                                cexists=1

			if cexists==0:
			    logging.info('Adding new attachment!')
			    aa = _add_attachment(attachment,isskey)

		    issue_obj_update.write(cr, uid, issueid.id, {'jira_attachments': attids}, context=context)
	    else:
		for attachment in attachments:
		    aa = _add_attachment(attachment,isskey)

		issue_obj_update.write(cr, uid, issueid.id, {'jira_attachments': attids}, context=context)

	    return True


	###get all issues from odoo - check if it was already transfered to jira.If no - transfer, if yes - check if there's anything to update.
	for issueid in project_issue_ids:
	    logging.info(issueid.id)
	    odoo_issue = self.get_project_issues(cr, uid, issueid.id, context=None)
	    name = odoo_issue.name
	    jira_id = odoo_issue.jira_id
	    jira_key = odoo_issue.jira_key
	    desc = odoo_issue.description
	    priority = odoo_issue.priority
	    odoo_jira_attachments = odoo_issue.jira_attachments

	    if desc != "":
		desc = name

	    ##if jira_id and jira_key are empty it means that this is a new issue, which we need to transfer to jira
	    if not jira_id and not jira_key:
		logging.info('jira_id and jira_key are empty - creating issue in JIRA app...')

		##need to check if issue was created from email. If so, we need to get mail body from mail_message table
                email = _get_mail(issueid.id)
		if email:
		    desc = re.sub("<.*?>", "",email.body)

		issue_dict = {
	    	    'project': {'key': jira_project_key.encode('utf-8')},
	    	    'summary': name.encode('utf-8'),
	    	    'description': desc.encode('utf-8'),
	    	    'issuetype': {'name': 'Bug'},
		    'priority': {'name': prioritymap[priority]},
		}

		new_issue = jira.create_issue(fields=issue_dict)

		##get issue id
		issid = new_issue.id
		isskey = new_issue.key
		issstatus = new_issue.fields.status.name
		#isslink = new_issue.fields.issuelinks

		isslink = self.get_jira_issue_link(cr, uid, isskey)
		logging.info(isslink)

		##save values from jira to odoo issue
		issue_obj = self.pool.get('project.issue')
		issue_obj.write(cr, uid, issueid.id, {'jira_key': isskey}, context=context)
		issue_obj.write(cr, uid, issueid.id, {'jira_id': issid}, context=context)
		issue_obj.write(cr, uid, issueid.id, {'jira_status': issstatus}, context=context)
		issue_obj.write(cr, uid, issueid.id, {'jira_link': isslink}, context=context)


                attachments = _get_attachments(issueid.id)
		att = _handle_attachments(attachments,odoo_jira_attachments,isskey,issue_obj)

	    ##jira_id and jira_key are filled. Update issues...
	    else:
		logging.info('Issue exists in JIRA application. Doing update...')

		issue_to_update = jira.issue(jira_key)
		jira_status = issue_to_update.fields.status.name
		jira_description = issue_to_update.fields.description
		jira_comments = [comment for comment in issue_to_update.fields.comment.comments]
		odoo_jira_status = odoo_issue.jira_status
		odoo_jira_description = odoo_issue.description
		odoo_jira_comments = odoo_issue.jira_comments
		odoo_jira_attachments = odoo_issue.jira_attachments
		odoo_stage_id = odoo_issue.stage_id.id
		
		issue_obj_update = self.pool.get('project.issue')

                attachments = _get_attachments(issueid.id)
		att = _handle_attachments(attachments,odoo_jira_attachments,jira_key,issue_obj_update)

		###Handling the comments
		commids=''
		for comment in jira_comments:
		    commids = comment.id+";"+commids

		if commids:
		    commids=commids[:-1]

		if odoo_jira_comments:
		    logging.info('Comments exists. Check and add only the new one!')
		    if odoo_jira_comments != commids:
			logging.info('Comments are NOT equals')
			commidtab=string.split(odoo_jira_comments, ';')

			###checking if comment id is already saved in database
	    		for comment in jira_comments:
			    cexists=0
			    for idtab in commidtab:
				if comment.id==idtab:
				    cexists=1
			
			    if cexists==0:
				comment = str(comment.author)+":: "+str(comment.body)
				issue_obj_update.message_post(cr, uid, issueid.id, body=_(comment), context=context)

			issue_obj_update.write(cr, uid, issueid.id, {'jira_comments': commids}, context=context)
		else:
		    issue_obj_update.write(cr, uid, issueid.id, {'jira_comments': commids}, context=context)
		    for comment in jira_comments:
			comment = str(comment.author)+":: "+str(comment.body)
			issue_obj_update.message_post(cr, uid, issueid.id, body=_(comment), context=context)

		if jira_description != odoo_jira_description:
		    ###if jira issue has no description it sends 'False' - need to eliminate this
		    if jira_description != 'False':
			###differences between descriptions. Doing update...(field+openchatter)
			issue_obj_update.write(cr, uid, issueid.id, {'description': jira_description.encode('utf-8')}, context=context)
			issue_obj_update.message_post(cr, uid, issueid.id, body=_("JIRA issue description has changed."), context=context)

		task_type_name=self.get_task_type_name(cr, uid, odoo_stage_id, context=None)
		current_odoo_state=self.get_task_type_state(cr, uid, odoo_stage_id, context=None)

		if (jira_status != current_odoo_state):
		    if current_odoo_state:
			###differencess between statuses. Doing update...(field+openchatter)
			##issue_obj_update.write(cr, uid, issueid.id, {'jira_status': jira_status}, context=context)
			##issue_obj_update.message_post(cr, uid, issueid.id, body=_("JIRA issue status has changed to "+str(jira_status)), context=context)

			task_type_id=self.get_task_id(cr, uid, jira_status, context=None)

			if task_type_id != 0:
			    issue_obj_update.write(cr, uid, issueid.id, {'jira_status': jira_status.encode('utf-8')}, context=context)
			    issue_obj_update.message_post(cr, uid, issueid.id, body=_("JIRA issue status has changed to "+jira_status.encode('utf-8')), context=context)

		    	    ###update issue status
		    	    issue_obj_update.write(cr, uid, issueid.id, {'stage_id': task_type_id}, context=context)
			else:
			    logging.info('1. Stage not updated! Mapping stage-state for '+jira_status.encode('utf-8')+' not set!')
		    else:
			logging.info('2. Stage not updated! Mapping stage-state for '+jira_status.encode('utf-8')+' not set!')

		    logging.info(odoo_issue.name)


  def get_task_type_state(self, cr, uid, stage_id, context=None):
    state = self.pool.get('project.task.type').search(cr, uid, [('id', '=', stage_id)])
    if state:
	task_type_state = self.pool.get('project.task.type').browse(cr, uid, state, context=context)

    return task_type_state.state


  def get_task_type_name(self, cr, uid, stage_id, context=None):
    task_type = self.pool.get('project.task.type').search(cr, uid, [('id', '=', stage_id)])
    if task_type:
	task_type_name = self.pool.get('project.task.type').browse(cr, uid, task_type, context=context)

    return task_type_name.name


  def get_task_id(self, cr, uid, jira_status, context=None):
    js = jira_status.encode('utf-8')
    task_type = self.pool.get('project.task.type').search(cr, uid, [('state', '=', js)])

    if task_type:
	task_type_id = self.pool.get('project.task.type').browse(cr, uid, task_type, context=context)
	task_type_id = task_type_id.id
    else:
	task_type_id = 0

    return task_type_id


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

