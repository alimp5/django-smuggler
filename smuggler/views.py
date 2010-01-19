# Copyright (c) 2009 Guilherme Gondim and contributors
#
# This file is part of Django Smuggler.
#
# Django Smuggler is free software under terms of the GNU Lesser
# General Public License version 3 (LGPLv3) as published by the Free
# Software Foundation. See the file README for copying conditions.

from django.core import serializers
from django.db.models import get_model
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from smuggler.forms import ImportDataForm
from smuggler.settings import SMUGGLER_FORMAT
from smuggler.utils import serialize_to_response

def export_data(request, app_label, model_label):
    model = get_model(app_label, model_label)
    objects = model._default_manager.all()
    filename = '%s-%s.%s' % (app_label, model_label, SMUGGLER_FORMAT)
    response = HttpResponse(mimetype="text/plain")
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return serialize_to_response(objects, response)

def import_data(request, app_label, model_label):
    if request.method == 'POST':
        form = ImportDataForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            if uploaded_file.multiple_chunks():
                data = file(uploaded_file.temporary_file_path(), 'r')
            else:
                data = uploaded_file.read()
            if uploaded_file.content_type == 'text/xml':
                file_ext = 'xml'
            elif uploaded_file.content_type == 'application/json':
                file_ext = 'json'
            else:
                # Fallback to "json" because on some tests the ``content_type``
                # of JSON files was "application/octet-stream".
                file_ext = 'json'
            objects = serializers.deserialize(file_ext, data)
            for obj in objects:
                obj.save()
            user_msg = _('Data imported with success.')
            request.user.message_set.create(message=user_msg)
            return HttpResponseRedirect('./')
    else:
        form = ImportDataForm()
    model = get_model(app_label, model_label)
    context = {
        'app_label': app_label,
        'form': form,
        'opts': model._meta,
    }
    return render_to_response(
        'smuggler/import_data_form.html',
        context,
        context_instance=RequestContext(request)
    )
