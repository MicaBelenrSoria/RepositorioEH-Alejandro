from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required #decorador para el login required
from django.contrib.auth import logout, authenticate, login
from django.db import connections,transaction
from django.test import override_settings
from django.shortcuts import render, redirect
from .models import *
from .forms import UserRegisterForm
from django.contrib import messages
from .forms import DocumentacionForm
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from datetime import datetime, timedelta
import json
import mercadopago
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import uuid
from .forms import UploadCertificateForm
import os
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
import zipfile
from django.core.mail import send_mail
import io
from django.core.files.storage import FileSystemStorage
import shutil
from .models import Documentacion

# Create your views here.
@login_required
def home(request):
    # Obtener el número de documento del usuario actual
    documento = request.user.username
    
    # Consultar la base de datos externa
    with connections['default1'].cursor() as cursor:
        cursor.execute("SELECT nombre, apellido, telefono FROM vw_web_alumnos WHERE documento = %s", [documento])
        result = cursor.fetchone()
    
    # Verificar si los datos personales están completos
    if result is None or any(field is None or field == '' for field in result):
        # Enviar por session el dato "documento" y redirigir al formulario "datos_personales" para completar los datos_personales
        request.session['documento'] = documento
        return redirect('datos_personales')
    
    # Renderizar la página de inicio si los datos personales están completos
    return render(request, 'home.html')

@login_required
def datos_personales(request):
    documento = request.session.get('documento', request.user.username)

    try:
        with connections['default1'].cursor() as cursor:
            cursor.execute("SELECT * FROM vw_web_alumnos WHERE documento = %s", [documento])
            resultado = cursor.fetchone()
        
        if resultado:
            id_alumno = resultado[0]
            form_user = AlumnoForm(initial={
                'apellido': resultado[1] if resultado[1] else '',
                'nombre': resultado[2] if resultado[2] else '',
                'dni': resultado[3] if resultado[3] else '',
                'fechanacimiento': resultado[4] if resultado[4] else '',
                'sexo': resultado[5] if resultado[5] else '',
                'domicilio': resultado[7] if resultado[7] else '',
                'codigopostal': resultado[8] if resultado[8] else '',
                'provincia': resultado[10] if resultado[10] else '',
                'telefono': resultado[11] if resultado[11] else '',
                'celular': resultado[12] if resultado[12] else '',
                'email': resultado[13] if resultado[13] else '',
                'colegio': resultado[30] if resultado[30] else '',
                'dificultadfisica': resultado[21] if resultado[21] else '',
                'tratamientopsicologico': resultado[22] if resultado[22] else '',
                'esalergico': resultado[47] if resultado[47] else '',
                'estemerosoaagua': resultado[26] if resultado[26] else '',
                'flotaenloprofundo': resultado[27] if resultado[27] else '',
                'nivel_ed': resultado[29] if resultado[29] else '',
                'observaciones': resultado[21] if resultado[21] else '',
                'preferenciaamigos': resultado[24] if resultado[24] else '',
                'padre': resultado[38] if resultado[38] else '',
                'padrecelular': resultado[39] if resultado[39] else '',
                'padreemail': resultado[40] if resultado[40] else '',
                'padredni': resultado[41] if resultado[41] else '',
                'madre': resultado[42] if resultado[42] else '',
                'madrecelular': resultado[43] if resultado[43] else '',
                'madreemail': resultado[44] if resultado[44] else '',
                'madredni': resultado[45] if resultado[45] else '',
                'utilizamicrocolonia': resultado[28] if resultado[28] else ''
            })
        else:
            form_user = AlumnoForm()

        niveles_disp = Nivel_educativo.objects.all()

        if request.method == 'POST':
            data_form = AlumnoForm(request.POST)
            if data_form.is_valid():
                data = data_form.cleaned_data
                with connections['default1'].cursor() as cursor:
                    cursor.execute(
                        """
                        EXEC SP_WEB_ALUMNOMODIFICACION %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        """,
                        [
                            id_alumno,
                            data['apellido'],
                            data['nombre'],
                            data['dni'],
                            data['fechanacimiento'],
                            data['sexo'],
                            data['domicilio'],
                            data['codigopostal'],
                            data['provincia'],
                            data['telefono'],
                            data['celular'],
                            data['email'],
                            data['dni'],  # USUARIOWEB
                            resultado[20],  # PASSWORDWEB
                            data['nivel_ed'],
                            data['colegio'],
                            data['dificultadfisica'],
                            data['tratamientopsicologico'],
                            data['esalergico'],
                            data['estemerosoaagua'],
                            data['flotaenloprofundo'],
                            data['observaciones'],
                            data['preferenciaamigos'],
                            data['padre'],
                            data['padrecelular'],
                            data['padreemail'],
                            data['padredni'],
                            data['madre'],
                            data['madrecelular'],
                            data['madreemail'],
                            data['madredni'],
                            0  # utilizamicrocolonia
                        ]
                    )
                return redirect('home')
            else:
                context = {'code': 500, 'message': data_form.errors}
                return render(request, 'errorhandler.html', context=context)

    except Exception as e:
        context = {'code': 500, 'message': str(e)}
        return render(request, 'errorhandler.html', context=context)

    return render(request, 'datos_personales.html', {
        'form': form_user,
        'niveles': niveles_disp,
        'documento': documento
    })


def sucess(request):
    return render(request, 'sucess.html')


def exit(request):
    logout(request)
    return redirect('home')


def register(request):

    data = {
        'form': UserRegisterForm()
    }

    if request.method == 'POST':
        user_creation_form = UserRegisterForm(data=request.POST)

        if user_creation_form.is_valid():
            user_creation_form.save()

            username = user_creation_form.cleaned_data['username']
            email = user_creation_form.cleaned_data['email']
            password = user_creation_form.cleaned_data['password1']
            dni = user_creation_form.cleaned_data['username']  # Assuming dni is stored in the username field

           
            crear_alumno_dbexterna(dni, email, username, password)

            user = authenticate(username=user_creation_form.cleaned_data['username'], password=user_creation_form.cleaned_data['password1'])
            login(request, user)
            return redirect('home')
        else:
            data['form'] = user_creation_form

    return render (request, 'registration/register.html',data)

#FORM INIT 
from django.shortcuts import render, redirect
from django.db import connections
from django import forms
from .models import Nivel_educativo
from datetime import datetime
from django.urls import reverse
from django.http import HttpResponseRedirect

class MyForm(forms.Form):
    fechanacimiento = forms.DateField(label='Fecha de Nacimiento', input_formats=['%Y-%m-%d'])

def my_view(request):
    if request.method == 'POST':
        form = MyForm(request.POST)
        if form.is_valid():
            # procesa los datos del formulario
            pass
    else:
        # Simulación de obtención de fecha de nacimiento desde la base de datos
        fecha_nacimiento = datetime.strptime('1900-01-01', '%Y-%m-%d').date()
        form = MyForm(initial={'fechanacimiento': fecha_nacimiento})

    return render(request, 'alumno_modificacion.html', {'form': form})

class AlumnoForm(forms.Form):
    nivel_ed = forms.IntegerField(label='Nivel educativo', required=False)
   # nivel_ed = forms.ChoiceField(label='Nivel Educativo', choices=Nivel_educativo.choices)
    apellido = forms.CharField(label='Apellido', max_length=500)
    nombre = forms.CharField(label='Nombre', max_length=500)
    dni = forms.CharField(label='DNI', max_length=500)
    fechanacimiento = forms.DateField(label='Fecha de Nacimiento')
    sexo = forms.CharField(label='Sexo', max_length=1)
    domicilio = forms.CharField(label='Domicilio', max_length=500, required=False)
    codigopostal = forms.CharField(label='Código Postal', max_length=500, required=False)
    provincia = forms.CharField(label='Provincia', max_length=500, required=False)
    telefono = forms.CharField(label='Teléfono', max_length=500, required=False)
    celular = forms.CharField(label='Celular', max_length=500, required=False)
    email = forms.EmailField(label='Email', required=False)
    colegio = forms.CharField(label='Colegio', max_length=500, required=False)
    dificultadfisica = forms.CharField(label='Dificultad Física', max_length=500, required=False)
    tratamientopsicologico = forms.CharField(label='Tratamiento Psicológico', max_length=500, required=False)
    esalergico = forms.CharField(label='Es Alergico', max_length=500, required=False)
    estemerosoaagua = forms.BooleanField(label='Estemeroso a Agua', required=False)
    flotaenloprofundo = forms.BooleanField(label='Flota en lo Profundo', required=False)    
    observaciones = forms.CharField(label='Observaciones', max_length=500, required=False)
    preferenciaamigos = forms.CharField(label='Preferencia Amigos', max_length=500, required=False)
    padre = forms.CharField(label='Padre', max_length=500, required=False)
    padrecelular = forms.CharField(label='Padre Celular', max_length=500, required=False)
    padreemail = forms.EmailField(label='Padre Email', required=False)
    padredni = forms.CharField(label='Padre DNI', max_length=500, required=False)
    madre = forms.CharField(label='Madre', max_length=500, required=False)
    madrecelular = forms.CharField(label='Madre Celular', max_length=500, required=False)
    madreemail = forms.EmailField(label='Madre Email', required=False)
    madredni = forms.CharField(label='Madre DNI', max_length=500, required=False)
    # new field
    # utilizamicrocolonia = forms.BooleanField(label='Utiliza microcolonia', required=False)


def elegir_alumno(request):
    dni = request.user.username

    consulta_alumno = f"SELECT * FROM vw_web_alumnos WHERE DOCUMENTO = '{dni}'"

    alumno = None
    id_alumno = None
    nivel_educativo_alumno = None

    with connections['default1'].cursor() as cursor:
        cursor.execute(consulta_alumno)
        resultado = cursor.fetchall()

        if resultado:
            alumno = resultado[0]
            id_alumno = alumno[0]

        else:
            resultado = []

    familiares = []
    datos_familiares = []
    nivel_educativo_familiares = []

    if id_alumno:
        consulta_familiares = f"EXEC SP_WEB_ALUMNOSFAMILIARES {id_alumno}"
        with connections['default1'].cursor() as cursor:
            cursor.execute(consulta_familiares)
            familiares_resultado = cursor.fetchall()
            print(f'familiares_resultado: {familiares_resultado}')

        familiares = [registro[0] for registro in familiares_resultado]
        print(f'familiares: {familiares}')

    if familiares:
        familiares_ids = ', '.join(map(str, familiares))
        consulta_datos_familiares = f"SELECT * FROM vw_web_alumnos WHERE IDALUMNO IN ({familiares_ids})"
        with connections['default1'].cursor() as cursor:
            cursor.execute(consulta_datos_familiares)
            datos_familiares = cursor.fetchall()
            print(f'datos_familiares: {datos_familiares}')
            cursor.close()

        nivel_educativo_familiares = [registro[29] for registro in datos_familiares]

    lista_datos = [(int(alumno[0]), nivel_educativo_alumno, alumno[1], alumno[2])] + [(int(familiar[0]), nivel, familiar[1], familiar[2]) for familiar, nivel in zip(datos_familiares, nivel_educativo_familiares)]

    if request.method == 'POST':
        seleccion_alumno = request.POST.get('alumno')
        print(f"Alumno elegido para modificacion: {seleccion_alumno}")
        url = reverse('alumno_modificacion') + f'?alumno={seleccion_alumno}'
        return HttpResponseRedirect(url)
    return render(request, 'elegir_alumno.html', {'datos': lista_datos, 'elegir_alumno': id_alumno })


def alumno_modificacion(request):
    id_alumno = request.GET.get('alumno')
    print(f"alumno elegido: {id_alumno}")

    consulta_user = f"SELECT * FROM vw_web_alumnos WHERE IDALUMNO = '{id_alumno}'"
    resultado = None
    try:
        with connections['default1'].cursor() as cursor:
            cursor.execute(consulta_user)
            resultado = cursor.fetchone()
            form_user = AlumnoForm(initial={
                    'apellido': resultado[1],
                    'nombre': resultado[2],
                    'dni': resultado[3],
                    'fechanacimiento': resultado[4],
                    'sexo': resultado[5],
                    'domicilio': resultado[7],
                    'codigopostal': resultado[8],
                    'provincia': resultado[10],
                    'telefono': resultado[11],
                    'celular': resultado[12],
                    'email': resultado[13],
                    'colegio': resultado[30],
                    'dificultadfisica': resultado[21],
                    'tratamientopsicologico': resultado[22],
                    'esalergico': resultado[47],
                    'estemerosoaagua': resultado[26],
                    'flotaenloprofundo': resultado[27],
                    'nivel_ed': resultado[29],
                    'observaciones': resultado[21],
                    'preferenciaamigos': resultado[24],
                    'padre': resultado[38],
                    'padrecelular': resultado[39],
                    'padreemail': resultado[40],
                    'padredni': resultado[41],
                    'madre': resultado[42],
                    'madrecelular': resultado[43],
                    'madreemail': resultado[44],
                    'madredni': resultado[45],
                    'utilizamicrocolonia': resultado[28]
            })
            cursor.close()

        niveles_disp = Nivel_educativo.objects.all()
        form = form_user

        data_dict = {
            'form': form,
            'seleccion_alumno': id_alumno,
            'niveles': niveles_disp}

        if request.method == 'POST':
            data_form = AlumnoForm(request.POST)
            if data_form.is_valid():
                data = data_form.cleaned_data

                sp_modificacion_sql = """
                            EXEC SP_WEB_ALUMNOMODIFICACION %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            """
                params = [
                        id_alumno,
                        data['apellido'],
                        data['nombre'],
                        data['dni'],
                        data['fechanacimiento'],
                        data['sexo'],
                        data['domicilio'],
                        data['codigopostal'],
                        data['provincia'],
                        data['telefono'],
                        data['celular'],
                        data['email'],
                        resultado[19],  # USUARIOWEB
                        resultado[20],  # PASSWORDWEB
                        data['nivel_ed'],
                        data['colegio'],
                        data['dificultadfisica'],
                        data['tratamientopsicologico'],
                        data['esalergico'],
                        data['estemerosoaagua'],
                        data['flotaenloprofundo'],
                        data['observaciones'],
                        data['preferenciaamigos'],
                        data['padre'],
                        data['padrecelular'],
                        data['padreemail'],
                        data['padredni'],
                        data['madre'],
                        data['madrecelular'],
                        data['madreemail'],
                        data['madredni'],
                        1  # utilizamicrocolonia
                ]
                print(f"params para sp modificacion: {params}")
                with connections['default1'].cursor() as cursor:
                    cursor.execute(sp_modificacion_sql, params)
                    cursor.close()
                return redirect('home')  # Reemplaza con tu URL de éxito
            else:
                context = {'code': 500, 'message': data_form.errors}
                return render(request, 'errorhandler.html', context=context)

        return render(request, 'alumno_modificacion2.html', context=data_dict)
    except Exception as e:
        context = {'code': 500, 'message': e}
        return render(request, 'errorhandler.html', context=context)

# @login_required
# def datos_personales(request):
#     if request.session.get('documento'):
#         documento = request.session.get('documento')
#     else:
#         documento = request.user.username

#     try:
#         with connections['default1'].cursor() as cursor:
#             cursor.execute("SELECT * FROM vw_web_alumnos WHERE DOCUMENTO = %s", [documento])
#             resultado = cursor.fetchone()
        
#         if resultado:
#             id_alumno = resultado[0]
#             form_user = AlumnoForm(initial={
#                 'apellido': resultado[1] if resultado[1] else '',
#                 'nombre': resultado[2] if resultado[2] else '',
#                 'dni': resultado[3] if resultado[3] else '',
#                 'fechanacimiento': resultado[4] if resultado[4] else '',
#                 'sexo': resultado[5] if resultado[5] else '',
#                 'domicilio': resultado[7] if resultado[7] else '',
#                 'codigopostal': resultado[8] if resultado[8] else '',
#                 'provincia': resultado[10] if resultado[10] else '',
#                 'telefono': resultado[11] if resultado[11] else '',
#                 'celular': resultado[12] if resultado[12] else '',
#                 'email': resultado[13] if resultado[13] else '',
#                 'colegio': resultado[30] if resultado[30] else '',
#                 'dificultadfisica': resultado[21] if resultado[21] else '',
#                 'tratamientopsicologico': resultado[22] if resultado[22] else '',
#                 'esalergico': resultado[47] if resultado[47] else '',
#                 'estemerosoaagua': resultado[26] if resultado[26] else '',
#                 'flotaenloprofundo': resultado[27] if resultado[27] else '',
#                 'nivel_ed': resultado[29] if resultado[29] else '',
#                 'observaciones': resultado[21] if resultado[21] else '',
#                 'preferenciaamigos': resultado[24] if resultado[24] else '',
#                 'padre': resultado[38] if resultado[38] else '',
#                 'padrecelular': resultado[39] if resultado[39] else '',
#                 'padreemail': resultado[40] if resultado[40] else '',
#                 'padredni': resultado[41] if resultado[41] else '',
#                 'madre': resultado[42] if resultado[42] else '',
#                 'madrecelular': resultado[43] if resultado[43] else '',
#                 'madreemail': resultado[44] if resultado[44] else '',
#                 'madredni': resultado[45] if resultado[45] else '',
#                 'utilizamicrocolonia': resultado[28] if resultado[28] else ''
#             })
#         else:
#             form_user = AlumnoForm()

#         niveles_disp = Nivel_educativo.objects.all()

#         if request.method == 'POST':
#             data_form = AlumnoForm(request.POST)
#             if data_form.is_valid():
#                 data = data_form.cleaned_data
#                 with connections['default1'].cursor() as cursor:
#                     cursor.execute(
#                         """
#                         EXEC SP_WEB_ALUMNOMODIFICACION %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
#                         """,
#                         [
#                             id_alumno,
#                             data['apellido'],
#                             data['nombre'],
#                             data['dni'],
#                             data['fechanacimiento'],
#                             data['sexo'],
#                             data['domicilio'],
#                             data['codigopostal'],
#                             data['provincia'],
#                             data['telefono'],
#                             data['celular'],
#                             data['email'],
#                             data['dni'],  # USUARIOWEB
#                             resultado[20],  # PASSWORDWEB
#                             data['nivel_ed'],
#                             data['colegio'],
#                             data['dificultadfisica'],
#                             data['tratamientopsicologico'],
#                             data['esalergico'],
#                             data['estemerosoaagua'],
#                             data['flotaenloprofundo'],
#                             data['observaciones'],
#                             data['preferenciaamigos'],
#                             data['padre'],
#                             data['padrecelular'],
#                             data['padreemail'],
#                             data['padredni'],
#                             data['madre'],
#                             data['madrecelular'],
#                             data['madreemail'],
#                             data['madredni'],
#                             0  # utilizamicrocolonia
#                         ]
#                     )
#                 return redirect('home')
#             else:
#                 context = {'code': 500, 'message': data_form.errors}
#                 return render(request, 'errorhandler.html', context=context)

#     except Exception as e:
#         context = {'code': 500, 'message': str(e)}
#         return render(request, 'errorhandler.html', context=context)

#     return render(request, 'datos_personales.html', {
#         'form': form_user,
#         'niveles': niveles_disp,
#         'documento': documento
#     })


# def alumno_modificacion(request):
#     form = None
#     dni = request.user.username

#     # Consulta para obtener datos del alumno
#     consulta_alumno = f"SELECT * FROM vw_web_alumnos WHERE DOCUMENTO = '{dni}'"
#     alumno = None
#     id_alumno = None
#     nivel_educativo_alumno = None

#     with connections['default1'].cursor() as cursor:
#         cursor.execute(consulta_alumno)
#         resultado = cursor.fetchall()

#         if resultado:
#             alumno = resultado[0]
#             id_alumno = alumno[0]  # Asumiendo que IDALUMNO es el primer campo en la consulta
#             nivel_educativo_alumno = alumno[29]
#         else:
#             resultado = []

#     familiares = []
#     datos_familiares = []
#     nivel_educativo_familiares = []

#     if id_alumno:
#         consulta_familiares = f"EXEC SP_WEB_ALUMNOSFAMILIARES {id_alumno}"
#         with connections['default1'].cursor() as cursor:
#             cursor.execute(consulta_familiares)
#             familiares_resultado = cursor.fetchall()
        
#         familiares = [registro[0] for registro in familiares_resultado]

#     if familiares:
#         familiares_ids = ', '.join(map(str, familiares))
#         consulta_datos_familiares = f"SELECT * FROM vw_web_alumnos WHERE IDALUMNO IN ({familiares_ids})"
#         with connections['default1'].cursor() as cursor:
#             cursor.execute(consulta_datos_familiares)
#             datos_familiares = cursor.fetchall()

#         nivel_educativo_familiares = [registro[29] for registro in datos_familiares]

#     lista_datos = [(int(alumno[0]), nivel_educativo_alumno, alumno[1], alumno[2])] + [(int(familiar[0]), nivel, familiar[1], familiar[2]) for familiar, nivel in zip(datos_familiares, nivel_educativo_familiares)]

#     niveles_disp = Nivel_educativo.objects.all()
#     niveles = [nivel for nivel in niveles_disp]

#     seleccion_alumno = None
#     if request.method == 'POST':
#         seleccion_alumno = request.POST.get('alumno')
#         if seleccion_alumno:
#             consulta_alumno = f"SELECT * FROM vw_web_alumnos WHERE IDALUMNO = {seleccion_alumno}"
#             with connections['default1'].cursor() as cursor:
#                 cursor.execute(consulta_alumno)
#                 alumno = cursor.fetchone()

#             if alumno:
#                 form = AlumnoForm(initial={
#                     'apellido': alumno[1],
#                     'nombre': alumno[2],
#                     'dni': alumno[3],
#                     'fechanacimiento': alumno[4],
#                     'sexo': alumno[5],
#                     'domicilio': alumno[7], 
#                     'codigopostal': alumno[8], 
#                     'provincia': alumno[10], 
#                     'telefono': alumno[11], 
#                     'celular': alumno[12], 
#                     'email': alumno[13],
#                     'colegio': alumno[30],
#                     'dificultadfisica': alumno[21],
#                     'tratamientopsicologico': alumno[22],
#                     'esalergico': alumno[47],
#                     'estemerosoaagua': alumno[26],
#                     'flotaenloprofundo': alumno[27],
#                     'niveleducativo': alumno[29],
#                     'observaciones': alumno[21],
#                     'preferenciaamigos': alumno[24],
#                     'padre': alumno[38],
#                     'padrecelular': alumno[39],
#                     'padreemail': alumno[40],
#                     'padredni': alumno[41],
#                     'madre': alumno[42],
#                     'madrecelular': alumno[43],
#                     'madreemail': alumno[44],
#                     'madredni': alumno[45],
#                     'utilizamicrocolonia': alumno[28]
#                 })
#             else:
#                 form = AlumnoForm()

#             form_update = AlumnoForm(request.POST)

#             if form_update.is_valid():
#                 data = form_update.cleaned_data
#                 seleccion_alumno = int(seleccion_alumno)
#                 with connections['default1'].cursor() as cursor:
#                     cursor.execute(
#                         """
#                         EXEC SP_WEB_ALUMNOMODIFICACION %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
#                         """,
#                         [
#                             seleccion_alumno,
#                             data['apellido'],
#                             data['nombre'],
#                             data['dni'],
#                             data['fechanacimiento'],
#                             data['sexo'],
#                             data['domicilio'],
#                             data['codigopostal'],
#                             data['provincia'],
#                             data['telefono'],
#                             data['celular'],
#                             data['email'],
#                             data['dni'], # USUARIOWEB
#                             alumno[20], # PASSWORDWEB
#                             data['nivel_ed'],
#                             data['colegio'],
#                             data['dificultadfisica'],
#                             data['tratamientopsicologico'],
#                             data['esalergico'],
#                             data['estemerosoaagua'],
#                             data['flotaenloprofundo'],
#                             data['observaciones'],
#                             data['preferenciaamigos'],
#                             data['padre'],
#                             data['padrecelular'],
#                             data['padreemail'],
#                             data['padredni'],
#                             data['madre'],
#                             data['madrecelular'],
#                             data['madreemail'],
#                             data['madredni'],
#                             1 # utilizamicrocolonia
#                         ]
#                     )
#                 return redirect('home')  # Reemplaza con tu URL de éxito
#             else:
#                 print(f"Errores de forms: {form_update.errors}")
#     else:
#         form = AlumnoForm()

#     return render(request, 'alumno_modificacion.html', {'form': form, 'datos': lista_datos, 'seleccion_alumno': seleccion_alumno, 'niveles': niveles})

#FORM FIN

#db remota
def crear_alumno_dbexterna(dni, email, username, password):

    apellido = ""
    nombre = dni
    dni = dni
    fechanacimiento = ""  # Año, mes, día
    sexo = ""
    domicilio = ""
    codigopostal = ""
    provincia = ""
    telefono = ""
    celular = ""
    email = email
    usuarioweb = username
    passwordweb = password
    idniveleducativo = 1
    colegio = ""

    consulta_alumno = f"""
    EXEC SP_WEB_ALUMNO 
        @APELLIDO = N'{apellido}', 
        @NOMBRE = N'{nombre}', 
        @DNI = N'{dni}', 
        @FECHANACIMIENTO = '{fechanacimiento}', 
        @SEXO = N'{sexo}', 
        @DOMICILIO = N'{domicilio}', 
        @CODIGOPOSTAL = N'{codigopostal}', 
        @PROVINCIA = N'{provincia}', 
        @TELEFONO = N'{telefono}', 
        @CELULAR = N'{celular}', 
        @EMAIL = N'{email}', 
        @USUARIOWEB = N'{usuarioweb}', 
        @PASSWORDWEB = N'{passwordweb}', 
        @IDNIVELEDUCATIVO = {idniveleducativo}, 
        @COLEGIO = N'{colegio}'
    """
    with connections['default1'].cursor() as cursor:
        cursor.execute(consulta_alumno)
    
    print("usuario creado exitosamente")


#db local
def crear_alumno(dni, email, username, password):
    with transaction.atomic(using='default2'):
        with connections['default2'].cursor() as cursor:
            # Verificar si ya existe un usuario con el mismo DNI
            cursor.execute('SELECT COUNT(*) FROM ALUMNOS WHERE USUARIO = %s', [dni])
            if cursor.fetchone()[0] > 0:
                return "Usuario con este DNI ya existe."

            # Obtener el próximo IDALUMNO
            cursor.execute('SELECT COALESCE(MAX(IDALUMNO), 0) + 1 FROM ALUMNOS')
            next_idalumno = cursor.fetchone()[0]

            # Insertar el nuevo registro con el próximo IDALUMNO
            consulta = '''
                INSERT INTO ALUMNOS (IDALUMNO, DNI, EMAIL, USUARIO, PASSWORD)
                VALUES (%s, %s, %s, %s, %s)
            '''
            cursor.execute(consulta, [next_idalumno, dni, email, username, password])
            return "Usuario creado exitosamente."

# Base de datos local
@login_required
def datos_alumno1(request):
    dni = request.user.username
    # Realizar la consulta SQL utilizando raw()
    consulta = f"SELECT * FROM ALUMNOS WHERE DNI = '{dni}'"
    with connections['default2'].cursor() as cursor:
        cursor.execute(consulta)
        resultado = cursor.fetchall()

    # Verificar si se encontraron resultados
    alumno = None
    for registro in resultado:
        alumno = registro
        break

    # Pasar los resultados a la plantilla
    return render(request, 'datos_alumno1.html', {'alumno': alumno})


    
# base de datos remota

@login_required
def actividades_por_nombre(request):
    sucursal = request.GET.get('sucursal', '')
    actividad_seleccionada = request.GET.get('actividad', '')

    actividades = []
    detalles_actividad = {}

    if sucursal:
        consulta_actividades = """
        SELECT DISTINCT NOMBRE
        FROM vw_web_actividades
        WHERE SUCURSAL = %s
        """
        with connections['default1'].cursor() as cursor:
            cursor.execute(consulta_actividades, [sucursal])
            actividades_tuplas = cursor.fetchall()
            actividades = [actividad[0] for actividad in actividades_tuplas]

    if actividad_seleccionada:
        consulta_detalles = """
        SELECT DIA, DESDE, HASTA
        FROM vw_web_actividades
        WHERE SUCURSAL = %s AND NOMBRE = %s
        ORDER BY DIA, DESDE
        """
        with connections['default1'].cursor() as cursor:
            cursor.execute(consulta_detalles, [sucursal, actividad_seleccionada])
            detalles_tuplas = cursor.fetchall()
            for dia, desde, hasta in detalles_tuplas:
                if dia not in detalles_actividad:
                    detalles_actividad[dia] = []
                detalles_actividad[dia].append({'desde': desde, 'hasta': hasta})
        
    context = {
        'actividades': actividades,
        'sucursal': sucursal,
        'actividad_seleccionada': actividad_seleccionada,
        'detalles_actividad': detalles_actividad
    }
    return render(request, 'actividades_por_nombre.html', context)

@login_required
def datos_alumno(request):
    dni = request.user.username

    # Consulta para obtener datos del alumno
    consulta_alumno = f"SELECT * FROM vw_web_alumnos WHERE DOCUMENTO = '{dni}'"
    alumno = None
    id_alumno = None

    with connections['default1'].cursor() as cursor:
        cursor.execute(consulta_alumno)
        resultado = cursor.fetchall()

        # Verificar si se encontraron resultados y obtener el ID del alumno
        if resultado:
            alumno = resultado[0]
            id_alumno = alumno[0]  # Asumiendo que IDALUMNO es el primer campo en la consulta
        else:
            resultado = []

    familiares = []
    datos_familiares = []

    if id_alumno:
        # Llamar al stored procedure para obtener los familiares
        consulta_familiares = f"EXEC SP_WEB_ALUMNOSFAMILIARES {id_alumno}"
        with connections['default1'].cursor() as cursor:
            cursor.execute(consulta_familiares)
            familiares_resultado = cursor.fetchall()
        
        # Procesar los datos de los familiares
        familiares = [registro[0] for registro in familiares_resultado]

    if familiares:
        # Crear una cadena de IDs separados por comas para la consulta SQL
        familiares_ids = ', '.join(map(str, familiares))
        
        # Consulta para obtener los datos de los familiares usando los IDs
        consulta_datos_familiares = f"SELECT * FROM vw_web_alumnos WHERE IDALUMNO IN ({familiares_ids})"
        with connections['default1'].cursor() as cursor:
            cursor.execute(consulta_datos_familiares)
            datos_familiares = cursor.fetchall()

    # Pasar los resultados a la plantilla
    context = {
        'alumno': alumno,
        'familiares': datos_familiares,
    }
    return render(request, 'datos_alumno.html', context)


@login_required
def seleccionar_alumno(request):
    dni = request.user.username
    alumno = None
    id_alumno = None
    familiares = []
    datos_familiares = []

    # Paso 1: Obtener los datos del alumno
    consulta_alumno = f"SELECT * FROM vw_web_alumnos WHERE DOCUMENTO = '{dni}'"
    with connections['default1'].cursor() as cursor:
        cursor.execute(consulta_alumno)
        resultado = cursor.fetchall()
        if resultado:
            alumno = resultado[0]
            id_alumno = alumno[0]

    # Paso 2: Obtener los familiares
    if id_alumno:
        consulta_familiares = f"EXEC SP_WEB_ALUMNOSFAMILIARES {id_alumno}"
        with connections['default1'].cursor() as cursor:
            cursor.execute(consulta_familiares)
            familiares_resultado = cursor.fetchall()
        familiares = [registro[0] for registro in familiares_resultado]

    # Paso 3: Obtener los datos de los familiares
    if familiares:
        familiares_ids = ', '.join(map(str, familiares))
        consulta_datos_familiares = f"SELECT * FROM vw_web_alumnos WHERE IDALUMNO IN ({familiares_ids})"
        with connections['default1'].cursor() as cursor:
            cursor.execute(consulta_datos_familiares)
            datos_familiares = cursor.fetchall()

    # Paso 4: Preparar las opciones para el formulario
    opciones = [(alumno[0], alumno[2]) for alumno in [alumno] + datos_familiares]

    # Paso 5: Manejo del formulario de selección
    if request.method == 'POST':
        select_form = DocumentacionForm(request.POST)
        if select_form.is_valid():
            selected_id = select_form.cleaned_data['id']
            return redirect('upload_image', alumno_id=selected_id)
    else:
        select_form = DocumentacionForm()
    select_form.fields['id'].choices = opciones

    # Paso 6: Renderizar la plantilla
    context = {
        'select_form': select_form
    }
    return render(request, 'seleccionar_alumno.html', context)

@login_required
def upload_image(request, alumno_id):
    alumno = Documentacion.objects.get(id=alumno_id)
    if request.method == 'POST':
        form = DocumentacionForm(request.POST, request.FILES, instance=alumno)
        if form.is_valid():
            form.save()
            return redirect('seleccionar_alumno')
    else:
        form = DocumentacionForm(instance=alumno)

    context = {
        'form': form
    }
    return render(request, 'upload_image.html', context)

def success(request):
    return render(request, 'success.html')



@login_required
def inscripcion_colonia(request):
    dni = request.user.username

    # Consulta para obtener datos del alumno
    consulta_alumno = f"SELECT * FROM vw_web_alumnos WHERE DOCUMENTO = '{dni}'"
    
    alumno = None
    id_alumno = None
    nivel_educativo_alumno = None

    with connections['default1'].cursor() as cursor:
        cursor.execute(consulta_alumno)
        resultado = cursor.fetchall()

        # Verificar si se encontraron resultados y obtener el ID del alumno
        if resultado:
            alumno = resultado[0]
            id_alumno = alumno[0]  # Asumiendo que IDALUMNO es el primer campo en la consulta
            nivel_educativo_alumno = alumno[29]
        else:
            resultado = []

    familiares = []
    datos_familiares = []
    nivel_educativo_familiares = []

    if id_alumno:
        # Llamar al stored procedure para obtener los familiares
        consulta_familiares = f"EXEC SP_WEB_ALUMNOSFAMILIARES {id_alumno}"
        with connections['default1'].cursor() as cursor:
            cursor.execute(consulta_familiares)
            familiares_resultado = cursor.fetchall()
        
        # Procesar los datos de los familiares
        familiares = [registro[0] for registro in familiares_resultado]
        

    if familiares:
        # Crear una cadena de IDs separados por comas para la consulta SQL
        familiares_ids = ', '.join(map(str, familiares))
        
        # Consulta para obtener los datos de los familiares usando los IDs
        consulta_datos_familiares = f"SELECT * FROM vw_web_alumnos WHERE IDALUMNO IN ({familiares_ids})"
        with connections['default1'].cursor() as cursor:
            cursor.execute(consulta_datos_familiares)
            datos_familiares = cursor.fetchall()

        nivel_educativo_familiares = [registro[29] for registro in datos_familiares]
        
    # Crear lista de datos combinando alumno y familiares
    lista_datos = [(int(alumno[0]), nivel_educativo_alumno, alumno[1], alumno[2])] + [(int(familiar[0]), nivel, familiar[1] , familiar[2]) for familiar, nivel in zip(datos_familiares, nivel_educativo_familiares)]


    # Obtener los parámetros seleccionados en el formulario
    alumno_seleccionado = request.GET.get('alumno', '0')    
    sucursal_seleccionada = request.GET.get('sucursal')
    mes_seleccionado = request.GET.get('mes')
    nivel_educ = request.GET.get('nivel_ed')

    #Todos los niveles educativos disponibles

    niveles_disp = Nivel_educativo.objects.all()


    # Obtener el nivel educativo del alumno seleccionado ------OBSOLETA------
    nivel_educativo_alumno_seleccionado = 0
    for dato in lista_datos:
        if int(alumno_seleccionado) == dato[0]:
            nivel_educativo_alumno_seleccionado = dato[1]
            break
    

    # Obtener la lista de vacantes disponibles para los parámetros seleccionados
    vacantes_disponibles = []
    if alumno_seleccionado and sucursal_seleccionada and mes_seleccionado:
        nivel_educativo = Nivel_educativo.objects.get(nombre=nivel_educ)
        sucursal = Sucursal.objects.get(nombre=sucursal_seleccionada)
        mes = Mes.objects.get(nombre=mes_seleccionado)

        vacantes = Vacante.objects.filter(
            sucursal=sucursal,
            mes=mes,
            nivel_educativo=nivel_educativo,
            cantidad_vacantes__gt=0
        )

        vacantes_disponibles = vacantes
    
    
    #CONSULTA ALUMNO SELECCIONADO NOMBRE Y APELLIDO
    consulta_nombre_apellido = f"SELECT * FROM vw_web_alumnos WHERE IDALUMNO = '{alumno_seleccionado}'"
    alumno1 = None
    nombre_apellido = None
    with connections['default1'].cursor() as cursor:
        cursor.execute(consulta_nombre_apellido)
        resultado1 = cursor.fetchall()

    if resultado1:
            alumno1 = resultado[0]
            nombre_apellido = alumno1[1] + " " + alumno1[2] # Asumiendo que IDALUMNO es el primer campo en la consulta
            
    else:
            resultado1 = []

          

    context = {
        'nombre_ap':nombre_apellido,
        'sucursal': Sucursal.objects.all(),
        'mes': Mes.objects.all(),
        'vacantes_disponibles': vacantes_disponibles,
        'niveles': niveles_disp,
        'seleccion_alumno': alumno_seleccionado,
        'seleccion_sucursal': sucursal_seleccionada,
        'seleccion_mes': mes_seleccionado,

        'niveles': niveles_disp,
        'datos': lista_datos,
        'alumno': alumno_seleccionado,
        
    }

    
    return render(request, 'inscripcion_colonia.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def mercadopago_checkout(request):
    if request.method == "POST":

        data = json.loads(request.body)
        items = data.get('items', [])

        # Configurar el SDK de MercadoPago
        sdk = mercadopago.SDK("APP_USR-853973566845719-050723-8d86db2bfd6f33ce8ea35ee4867bfd11-30190833")
        
        # Calcular la fecha de expiración (inicio actual + 3 días)
        now = datetime.now()
        expiration_date = now + timedelta(days=3)

        # Formatear la fecha de expiración en formato ISO 8601
        expiration_date_iso = expiration_date.strftime('%Y-%m-%dT%H:%M:%S.000-04:00')

        # Crear la preferencia de pago
        preference_data = {
            "items": [
                {
                    "id": f"{uuid.uuid4()}",
                 "title": f"Colonia {item['semana']} turno {item['turno']}, Alumno: {item['nombres_apellidos']},  DNI: {item['dni']}, Nivel: {item['nivel_ed']}  ",
                    "currency_id": "ARS",
                    "description": f"Inscripcion Colonia {item['mes']}, {item['semana']} turno {item['turno']}, Alumno: {item['nombres_apellidos']} con Nro DNI: {item['dni']}",
                    "category_id": "art",
                    "quantity": 1,
                    "unit_price": int(item["reserva"]) + int(item["matricula"])
                } for index, item in enumerate(items)
            ],

            "payer": {
                "name": f"{items[0]['nombres_apellidos']}",
                "surname": f"{items[0]['dni']}"
            },
            "back_urls": {
                "success": "https://hipocampo.dimpera.com/sucess/",
                "failure": "http://www.failure.com",
                "pending": "http://www.pending.com"
            },
            "auto_return": "approved",
            "notification_url": "https://hipocampo.dimpera.com/mercadopago_webhook/",
            "statement_descriptor": "HCP",
            "external_reference": f"{items[0]['alumno']}",
            "expires": True,
            "expiration_date": expiration_date_iso
        }

        preference_response = sdk.preference().create(preference_data)
        preference_id = preference_response["response"]["id"]

        return JsonResponse({"preference_id": preference_id})

@csrf_exempt
def mercadopago_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        topic = data.get('topic')
        
        pago_id = data['data']['id']
        sdk = mercadopago.SDK('APP_USR-853973566845719-050723-8d86db2bfd6f33ce8ea35ee4867bfd11-30190833')

        info_pago = sdk.payment().get(pago_id)
        detalle_pago = info_pago['response']

        estado_pago = detalle_pago['status']
        if estado_pago == 'approved':
            estado = "PAGADO"

        elif estado_pago == 'rejected' or estado_pago == 'cancelled':
            estado = "CANCELADO"

        if topic:
            estado = "PENDIENTE"
            if topic == 'payment':
                
                alumno_id = detalle_pago.get('external_reference')
                alumno = Documentacion.objects.get(id=alumno_id)

                for item in detalle_pago['additional_info']['items']:
                    Pagos.objects.create(
                        dni=item.get('dni', ''),
                        nombres_apellidos=item.get('nombres_apellidos', ''),
                        descripcion=item.get('description', ''),
                        alumno=alumno,
                        pago_id=pago_id,
                        estado=estado,
                        total_pagado=int(item.get('transaction_amount', 0)),
                        titulo=item.get('title', ''),
                        cantidad=int(item.get('quantity', 0)),
                        precio=item.get('unit_price', 0.0),
                        topic=topic,
                    )

                vacantes = Vacante.objects.filter(id=int(data[0].get('vacante_id', 0))).first()
                if vacantes:
                    if vacantes.cantidad_vacantes > 0: 
                        vacantes.cantidad_vacantes -= 1
                        vacantes.save()
                    else:
                        print("No se pueden restar vacantes, cantidad actual es 0")
                else:
                    print("Vacante no encontrada")

            else:
                Pagos.objects.create(
                    dni=detalle_pago.get('payer', {}).get('surname', {}),
                    nombres_apellidos=detalle_pago.get('payer', {}).get('name', ''),
                    alumno=None,
                    pago_id=None,
                    estado=estado,
                    total_pagado=int(detalle_pago.get('transaction_amount', 0)),
                    titulo=detalle_pago.get('description', ''),
                    topic=topic,
                )

        return HttpResponse('OK')

    else:
        return HttpResponse('El metodo no es aceptado, solo se permite metodos POST', status=405)


@login_required
def upload_certificate(request):
    if request.method == 'POST':
        form = UploadCertificateForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            dni = user.username
            date_str = datetime.now().strftime('%d%m%Y_%H%M%S')
            
            def rename_and_save_file(file, prefix):
                ext = os.path.splitext(file.name)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    new_name = f"{dni}_{date_str}_{prefix}{ext}"
                    directory = os.path.join(settings.MEDIA_ROOT, 'certificates')
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    file_path = os.path.join(directory, new_name)
                    with open(file_path, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    return new_name
                return None
            
            if 'medical_certificate' in request.FILES:
                medical_certificate = rename_and_save_file(request.FILES['medical_certificate'], 'AM')
            
            if 'health_insurance_card' in request.FILES:
                health_insurance_card = rename_and_save_file(request.FILES['health_insurance_card'], 'OS')
            
            return redirect('upload_success')
    else:
        form = UploadCertificateForm()
    
    return render(request, 'upload_certificate.html', {'form': form})

def upload_success(request):
    return render(request, 'upload_success.html')



def gestion_archivos_staff(request):
    # Lógica de la vista aquí
    return render(request, 'gestion_archivos_staff.html')


@staff_member_required
def download_media(request):
    media_folder = settings.MEDIA_ROOT
    zip_filename = os.path.join(settings.BASE_DIR, 'media.zip')

    # Verifica si la carpeta media contiene archivos
    has_files = False
    for foldername, subfolders, filenames in os.walk(media_folder):
        if filenames:
            has_files = True
            break

    # Si la carpeta está vacía, no procede con la descarga
    if not has_files:
        messages.error(request, "La carpeta MEDIA no se descarga porque está vacía.")
        return redirect('admin:index')

    # Crear el archivo ZIP
    with zipfile.ZipFile(zip_filename, 'w') as zip_file:
        for foldername, subfolders, filenames in os.walk(media_folder):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                zip_file.write(file_path, os.path.relpath(file_path, media_folder))

    # Devolver el archivo ZIP como respuesta
    with open(zip_filename, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename=media.zip'
        return response

    return response

@staff_member_required
def delete_media(request):
    media_root = settings.MEDIA_ROOT

    if request.method == "POST":
        if os.path.exists(media_root):
            try:
                shutil.rmtree(media_root)
                os.makedirs(media_root)  
                messages.success(request, "El contenido de la carpeta MEDIA ha sido eliminado exitosamente.")
            except Exception as e:
                messages.error(request, f"Error al eliminar el contenido de la carpeta MEDIA: {e}")
        else:
            messages.error(request, "La carpeta MEDIA no existe.")
        
        return redirect('admin:index')

    return redirect('confirm_delete_media')
    
@staff_member_required
def confirm_delete_media(request):
    if request.method == 'POST':
        media_root = settings.MEDIA_ROOT
        for root, dirs, files in os.walk(media_root):
            for file in files:
                file_path = os.path.join(root, file)
                os.remove(file_path)
        return redirect('admin:index')  
    else:
        return render(request, 'confirm_delete_media.html')

@staff_member_required
def accept_image(request, image_name):
    media_root = settings.MEDIA_ROOT
    original_file_path = os.path.join(media_root, 'certificates', image_name)

    if os.path.exists(original_file_path):
        accepted_folder = os.path.join(media_root, 'certificates', 'documentacion_aceptada')
        if not os.path.exists(accepted_folder):
            os.makedirs(accepted_folder)
        new_file_name = image_name.replace('.', '_ok.')
        new_file_path = os.path.join(accepted_folder, new_file_name)
        os.rename(original_file_path, new_file_path)
        
        messages.success(request, f"Imagen aceptada y movida a 'documentacion_aceptada' como {new_file_name}.")
    else:
        messages.error(request, f"El archivo no se encuentra en el directorio de medios.")

    return redirect('listar_imagenes')


@staff_member_required
def reject_image(request, image_name):
    media_root = settings.MEDIA_ROOT
    original_file_path = os.path.join(media_root, 'certificates', image_name)

    if os.path.exists(original_file_path):
        rejected_folder = os.path.join(media_root, 'certificates', 'documentacion_rechazada')
        if not os.path.exists(rejected_folder):
            os.makedirs(rejected_folder)
        new_file_path = os.path.join(rejected_folder, image_name)
        os.rename(original_file_path, new_file_path)

        # motivo del rechazo
        if 'AM' in image_name:
            motivo = "Fue rechazado el apto medico provisto para el alumno. Por favor contactarse con la escuela."
        elif 'OS' in image_name:
            motivo = "Fue rechazado el carnet de obra social provisto para el alumno. Por favor contactarse con la escuela."
        else:
            motivo = "Motivo no especificado."

        notificacion_rechazo(image_name, motivo)

        messages.success(request, f"Imagen rechazada, movida a 'documentacion_rechazada', y notificación enviada por correo.")
    else:
        messages.error(request, f"El archivo no se encuentra en el directorio de medios.")

    return redirect('listar_imagenes')

import logging

logger = logging.getLogger(__name__)

def notificacion_rechazo(image_name, motivo):
    print("Intentando enviar correo...")  # Agregar este print
    asunto = "Notificación de rechazo de imagen"
    mensaje = f"Su imagen {image_name} ha sido rechazada. Motivo: {motivo}"
    remitente = settings.DEFAULT_FROM_EMAIL
    destinatario = [remitente]

    try:
        send_mail(asunto, mensaje, remitente, destinatario, fail_silently=False)
        print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar la notificación de rechazo: {e}")


@staff_member_required
def index(request):
    media_root = settings.MEDIA_ROOT
    media_url = settings.MEDIA_URL
    images_by_alumno = {}

    for root, dirs, files in os.walk(media_root):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')) and not file.endswith('-ok.jpg') and not file.endswith('-ok.png') and not file.endswith('-ok.jpeg'):
                partes_nombre = file.split('_')
                if len(partes_nombre) > 1:
                    alumno_id = partes_nombre[0]
                    if alumno_id not in images_by_alumno:
                        images_by_alumno[alumno_id] = []
                    images_by_alumno[alumno_id].append({
                        'name': file,
                        'url': os.path.join(media_url, os.path.relpath(os.path.join(root, file), media_root))
                    })

    return render(request, 'admin/index.html', {'images_by_alumno': images_by_alumno})

@staff_member_required
def listar_imagenes(request):
    media_root = settings.MEDIA_ROOT
    media_url = settings.MEDIA_URL
    images_by_alumno = {}
    displayed = False

    for root, dirs, files in os.walk(os.path.join(media_root, 'certificates')):
        for file in files:
            if 'documentacion_aceptada' not in root and 'documentacion_rechazada' not in root:
                partes_nombre = file.split('_')
                if len(partes_nombre) > 1:
                    alumno_id = partes_nombre[0]
                    if alumno_id not in images_by_alumno:
                        images_by_alumno[alumno_id] = []
                    images_by_alumno[alumno_id].append({
                        'name': file,
                        'url': os.path.join(media_url, os.path.relpath(os.path.join(root, file), media_root))
                    })

    return render(request, 'listar_imagenes.html', {'images_by_alumno': images_by_alumno})


@staff_member_required
def consultar_archivos(request):
    media_root = settings.MEDIA_ROOT
    certificates_folder = os.path.join(media_root, 'certificates')

    accepted_images = {}
    rejected_images = {}
    pending_images = {}

    for root, dirs, files in os.walk(certificates_folder):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Verificar si la imagen está en la carpeta 'documentacion_aceptada'
            if 'documentacion_aceptada' in root:
                alumno_id = file.split('_')[0]
                accepted_images.setdefault(alumno_id, []).append({
                    'url': os.path.join(settings.MEDIA_URL, 'certificates', 'documentacion_aceptada', file),
                    'name': file
                })
            
            # Verificar si la imagen está en la carpeta 'documentacion_rechazada'
            elif 'documentacion_rechazada' in root:
                alumno_id = file.split('_')[0]
                rejected_images.setdefault(alumno_id, []).append({
                    'url': os.path.join(settings.MEDIA_URL, 'certificates', 'documentacion_rechazada', file),
                    'name': file
                })
            
            # Asumir que si no está en 'documentacion_aceptada' o 'documentacion_rechazada', es una imagen pendiente
            else:
                alumno_id = file.split('_')[0]
                pending_images.setdefault(alumno_id, []).append({
                    'url': os.path.join(settings.MEDIA_URL, 'certificates', file),
                    'name': file
                })

    context = {
        'accepted_images': accepted_images,
        'rejected_images': rejected_images,
        'pending_images': pending_images,
    }

    return render(request, 'consultar_archivos.html', context)


@staff_member_required
def descargar_contenido_media(request):
    # Crear un archivo ZIP en memoria
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        media_root = settings.MEDIA_ROOT

        # Recorrer los archivos y añadirlos al ZIP
        for root, dirs, files in os.walk(media_root):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, media_root)
                zf.write(file_path, relative_path)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=media_content.zip'

    return response

from django.core.mail import send_mail
from django.http import HttpResponse

def send_test_email(request):
    try:
        send_mail(
            'Asunto del correo de prueba',
            'Este es el cuerpo del correo de prueba.',
            'micabelenrs@gmail.com',  # De
            ['micabelenrs@gmail.com'],  # Para
            fail_silently=False,
        )
        return HttpResponse('Correo de prueba enviado.')
    except Exception as e:
        return HttpResponse(f"Error al enviar el correo: {e}")

from django.contrib.auth import views as auth_views

@login_required
def custom_password_reset_view(request):
    
    if not request.user.is_superuser and not request.user.is_staff:
        return auth_views.PasswordResetView.as_view(
            template_name='registration/custom_password_reset_form.html'
        )(request)
    else:
       
        return redirect('home') 