from django.contrib import admin
from django.urls import path
from .views import home, elegir_alumno, alumno_modificacion, actividades_por_nombre, exit, datos_alumno, datos_alumno1,register,seleccionar_alumno,sucess,upload_image,inscripcion_colonia,mercadopago_checkout,mercadopago_webhook, download_media, delete_media, accept_image, index, reject_image, confirm_delete_media, listar_imagenes, consultar_archivos, descargar_contenido_media
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
    path('admin/download-media/', views.download_media, name='admin_download_media'),
    path('admin/delete_media/', views.delete_media, name='admin_delete_media'),
    path('admin/confirm-delete-media/', views.confirm_delete_media, name='confirm_delete_media'),
    path('accept-image/<str:image_name>/', views.accept_image, name='accept_image'),
    path('reject-image/<str:image_name>/', views.reject_image, name='reject_image'),
    path('admin/', admin.site.urls, name='custom_admin'),
    path('listar-imagenes/', views.listar_imagenes, name='listar_imagenes'),
    path('consultar-archivos/', consultar_archivos, name='consultar_archivos'),
    path('descargar-contenido-media/', descargar_contenido_media, name='descargar_contenido_media'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
