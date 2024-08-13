from django.db import models



class Documentacion(models.Model):
    id = models.IntegerField(primary_key=True)
    imagen = models.ImageField(upload_to='imagenes/', null=True, blank=True, max_length=255)
    tiene_imagen = models.BooleanField(default=False)

    def __str__(self):
        return f'Alumno {self.id}'
    

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self):
        return self.nombre

class Turno(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self):
        return self.nombre

class Mes(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self):
        return self.nombre

class Semana(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self):
        return self.nombre

class Nivel_educativo(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self):
        return self.nombre

class Vacante(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    nivel_educativo = models.ForeignKey(Nivel_educativo, on_delete=models.CASCADE)
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE)
    mes = models.ForeignKey(Mes, on_delete=models.CASCADE)
    semana = models.ForeignKey(Semana, on_delete=models.CASCADE)
    cantidad_vacantes = models.PositiveIntegerField()

    

    def __str__(self):
        return f'{self.sucursal} - {self.nivel_educativo} - {self.turno} - {self.mes} - {self.semana} - Vacantes: {self.cantidad_vacantes}'
    

class Pagos(models.Model):
    
   
    estado = models.CharField(max_length=50, blank=True, null=True)
    titulo = models.CharField(max_length=512, blank=True, null=True)
    
    def __str__(self):
        return f'{self.estado} - {self.titulo} ' 