from django.urls import path
from .views import home, elegir_alumno, alumno_modificacion, actividades_por_nombre, exit, datos_alumno, datos_alumno1, register, seleccionar_alumno, sucess, upload_image, inscripcion_colonia, mercadopago_checkout, mercadopago_webhook, upload_certificate,upload_success
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', home, name='home'),
    path('actividades_por_nombre/', actividades_por_nombre, name='actividades_por_nombre'),
    path('datos_alumno/', datos_alumno, name='datos_alumno'),
    path('datos_alumno1/', datos_alumno1, name='datos_alumno1'),
    path('inscripcion_colonia/', inscripcion_colonia, name='inscripcion_colonia'),
    path('register/', register, name='register'),
    path('seleccionar_alumno/', seleccionar_alumno, name='seleccionar_alumno'),
    path('elegir_alumno/', elegir_alumno, name='elegir_alumno'),
    path('alumno_modificacion/', alumno_modificacion, name='alumno_modificacion'),
    path('upload-image/<int:alumno_id>/', upload_image, name='upload_image'),
    path('sucess/', sucess, name='sucess'),
    path('logout/', exit, name='exit'),
    path('mercadopago_checkout/', mercadopago_checkout, name='mercadopago_checkout'),
    path('mercadopago_webhook/', mercadopago_webhook, name='mercadopago_webhook'),
    path('upload-certificate/', views.upload_certificate, name='upload_certificate'),
    path('upload-success/', views.upload_success, name='upload_success'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
