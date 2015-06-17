# -*- coding: utf-8 -*-
##############################################################################

from openerp.osv import fields, osv

JIRA_SERVER = 'jira_server'
JIRA_PROTOCOL = 'jira_protocol'
JIRA_USERNAME = 'jira_username'
JIRA_PASSWORD = 'jira_password'
PROTOCOLS = [('http','http'),('https','https')]

class jira_configuration(osv.osv_memory):
    _inherit = 'project.config.settings'
    _description = 'JIRA Connection Settings'

    _columns = {
	JIRA_PROTOCOL : fields.selection(PROTOCOLS, 'Protocol'),
        JIRA_SERVER: fields.char('Link to JIRA application', size=64, required=True),
	JIRA_USERNAME : fields.char('Username', required=True),
	JIRA_PASSWORD : fields.char('Password', required=True),
    }

    def get_default_jira_server(self, cr, uid, ids, context=None):
        return {
            JIRA_SERVER:
                self.pool.get('ir.config_parameter').get_param(cr, uid, JIRA_SERVER)
        }


    def set_jira_server(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids)
        config = config and config[0]
        val = '%s' % config.jira_server or False
        self.pool.get('ir.config_parameter').set_param(cr, uid, JIRA_SERVER, val)
        return JIRA_SERVER


    def get_default_jira_protocol(self, cr, uid, ids, context=None):
        return {
            JIRA_PROTOCOL:
                self.pool.get('ir.config_parameter').get_param(cr, uid, JIRA_PROTOCOL)
        }


    def set_jira_protocol(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids)
        config = config and config[0]
        val = '%s' % config.jira_protocol or False
        self.pool.get('ir.config_parameter').set_param(cr, uid, JIRA_PROTOCOL, val)
        return JIRA_PROTOCOL


    def get_default_jira_username(self, cr, uid, ids, context=None):
        return {
            JIRA_USERNAME:
                self.pool.get('ir.config_parameter').get_param(cr, uid, JIRA_USERNAME)
        }

    def set_jira_username(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids)
        config = config and config[0]
        val = '%s' % config.jira_username or False
        self.pool.get('ir.config_parameter').set_param(cr, uid, JIRA_USERNAME, val)
        return JIRA_USERNAME


    def get_default_jira_password(self, cr, uid, ids, context=None):
        return {
            JIRA_PASSWORD:
                self.pool.get('ir.config_parameter').get_param(cr, uid, JIRA_PASSWORD)
        }

    def set_jira_password(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids)
        config = config and config[0]
        val = '%s' % config.jira_password or False
        self.pool.get('ir.config_parameter').set_param(cr, uid, JIRA_PASSWORD, val)
        return JIRA_PASSWORD
