This module restores the `state` fields to Project Stages, removed in Odoo 8.0.

For some use cases it‘s necessary to be able to map the multiple Stages into 
a few broad groups.

For example, this can allow to define automated actions and business logic for 
Tasks not yet “Started”, knowing that “Started” means different Stages in 
different Projects.

They project states was adopted from the ones in the original module:
_TASK_STATE = [
    ('draft', 'New'),
    ('open', 'In Progress'),
    ('pending', 'Pending'),
    ('done', 'Done'),
    ('cancelled', 'Cancelled')]

We have adopted this list exactly to the workflow status the customer
have defined in their preferred VCS:

_TASK_STATE = [
    ('open', 'Open'),
    ('progress', 'In Progress'),
    ('reopened', 'Reopened'),
    ('resolved', 'Resolved'),
    ('closed', 'Closed')]
