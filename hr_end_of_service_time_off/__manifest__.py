# -*- coding: utf-8 -*-
{
    'name': "HR End Of Service Time Off",
    'summary': """HR End Of Service  Time Off""",
    'author': "Crevisoft Corporate",
    'website': "https://www.crevisoft.com",

    'category': 'Human Resources',
    'version': '0.1',

    'depends': ['hr_end_of_service', 'hr_holidays', 'hr_advanced'],

    # always loaded
    'data': [
        'data/salary_rules.xml',
        'views/hr_end_service_views.xml'
    ]
}
