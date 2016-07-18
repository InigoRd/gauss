# -*- coding: utf-8 -*-

import datetime
from dateutil.rrule import rrule, MONTHLY, DAILY
from django.template import Library

register = Library()


@register.filter
def multiply(value, arg):
    return value*arg

@register.filter
def days(duration):
    return str(duration.days + float(duration.seconds)/3600/24).replace(',', '.')
# """
# It is suposed that a worker works 8 hours per day
# :param gtask: Gtask instance
# :return: Integer indicating the number of working days required to finish the task
# """



@register.filter
def hours(duration):
   return duration.days*8 + duration.seconds/3600