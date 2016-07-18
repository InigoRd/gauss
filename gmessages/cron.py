# -*- coding: utf-8 -*-
from datetime import datetime
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import kronos
from gauss.rutas import MEDIA_ADJUNTOS
from mensajes.models import Mensaje_cola, Aviso


@kronos.register('*/2 * * * *')
def mail_mensajes_cola():
    mensajes_cola = Mensaje_cola.objects.filter(enviado=False)

    if len(mensajes_cola) > 0:
        mensaje = mensajes_cola[0].mensaje
        direcciones = mensajes_cola[0].receptores.split(';')
        mensajes_cola[0].enviado = True
        mensajes_cola[0].save()

        nom = mensaje.emisor.alias if mensaje.emisor.alias else mensaje.emisor.gauser.get_full_name()
        html_mensaje = render_to_string('template_correo.html', {'mensaje': mensaje})
        if not mensaje.mensaje_texto: #Si no hay plain text lo creo a partir del mensaje html
            mensaje.mensaje_texto = strip_tags(mensaje.mensaje)
            mensaje.save()
        texto_mensaje = render_to_string('template_correoPlainText.html', {'mensaje': mensaje})
        # email = EmailMessage(mensaje.asunto, html_mensaje.encode('utf-8'),
        #                      '%s <gauss@gaumentada.es>' % (nom), bcc=direcciones,
        #                      headers={'Reply-To': mensaje.emisor.gauser.email})
        email = EmailMultiAlternatives(mensaje.asunto, texto_mensaje.encode('utf-8'),
                             '%s <gauss@gaumentada.es>' % (nom), bcc=direcciones,
                             headers={'Reply-To': mensaje.emisor.gauser.email})
        email.attach_alternative(html_mensaje, 'text/html')
        for adjunto in mensaje.adjuntos.all():
            email.attach_file(adjunto.fichero.url.replace('/media/adjuntos/', MEDIA_ADJUNTOS))
        # email.content_subtype = "html"
        email.send()
        fecha = datetime.now()
        texto = 'Correo enviado a %d destinatarios (id de Mesaje_cola: %s)' % (len(direcciones), mensajes_cola[0].id)
        Aviso.objects.create(usuario=mensaje.emisor, aviso=texto, fecha=fecha, aceptado=True, link='')
        # Creamos un aviso en caso de que se haya enviado por completo el mensaje, esto es cuando mensaje_cola.ultima_parte sea True
        if mensajes_cola[0].ultima_parte:
            fecha_string = fecha.strftime("%d-%m-%Y %H:%M:%S")
            num_mails = mensajes_cola[0].mensaje.receptores.all().count()
            t = '' if num_mails == 1 else 's'
            texto = 'Correo enviado correctamente a %d destinatario%s (%s)' %(num_mails, t, fecha_string)
            Aviso.objects.create(usuario=mensaje.emisor, aviso=texto, fecha=fecha, aceptado=False, link='')