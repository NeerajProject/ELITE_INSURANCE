# -*- coding: utf-8 -*-
{
    'name': 'Templates - Odoo screens-Elite Design',
    'version': '1.163',
    'author': 'Tecfuge Business Solutions',
    "website": "https://www.tecfuge.com/",
    'summary': 'Templates - Odoo screens-Elite_Design',
    'description': """
     """,
    'depends': [
        'base',
        'project',
        'helpdesk',
        'account',
        'account_accountant',
        'crm',
        'website',
        'product',
        'documents',
        'tecfuge_ebs_portal',
        'tecfuge_ebs_insurance',
        'fleet',
        'hr_appraisal',
        'utm'
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/res_commission_payable.xml'

    ],
    'assets': {

         },
    'images': [],
    'demo': [],
    'jquery': True,
    'bootstrap': True,
    'auto_install': False,
    'installable': True,
    'license': 'OPL-1',
}
