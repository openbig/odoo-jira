# -*- encoding: utf-8 -*-
##############################################################################
#
#    project_issue_jira
#    (C) 2015 big-consulting GmbH
#    (C) 2015 OpenGlobe
#    (C) 2015 Cirrus
#    Author: Agnieszka Kulpa (Cirrus)
#    Author: Thorsten Vocks (OpenBIG.org)
#    Author: Mikołaj Dziurzyński (OpenGlobe)
#
#    All Rights reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Project Issue Jira",
    'version': '0.1',
    'summary': """Jira Issue Connector""",
    'description': """Issue escalation from Odoo to JIRA""",
    'author': "OpenBIG.org",
    'website': "http://www.openbig.org",
    'description': """

Issue synchronisation with JIRA
=====================================

JIRA is a very popular ticket and project management 
software used by many software developers worldwide.

Define your connection to JIRA
-------------------------------

At first you have to define the connection to your JIRA server. 
This can be JIRA online or a on-premise installation of the 
famous ticket software from Atlassian.

Define JIRA workflow stages
---------------------------

You should define exactlly the same project stages as you have 
in JIRA to benefit from backwards synchronisation of stages from 
JIRA to Odoo. You may also have to define priorities in JIRA 
for the case some Odoo priorities are different. F.e. "Minor" 
and "Major" may be not the priorities you have defined in JIRA.

Map the JIRA project
--------------------

Enter the JIRA project code before you start to 
forward new Odoo issues to JIRA.

Start the synchronisation
--------------------------

Click on the button "Synch JIRA now" to start the scheduler in 
the background. By default every 5 minutes the new issues and 
stages will be synchronised. 

Open a link to the connected JIRA issue
----------------------------------------

After successfull synchronisation of tickets you can open 
the connected ticket in JIRA by clicking on the JIRA 
issue link. 

Future improvements
-------------------

The modules currently is limited to most essential fields. 
It can be further extended.


Contributors
============
* Agnieszka Kulpa (Cirrus)
* Thorsten Vocks (OpenBIG.org)
* Mikołaj Dziurzyński (OpenGlobe)

    """,
    'category': 'Project',
    'depends': [
    'project',
    'project_state_stage_customization',
    ],
    'data': [
	'project_issue_jira.xml',
	'jira_config_view.xml',
    ],
    'demo': [],
    'license': 'AGPL-3',
    'installable': True,
}