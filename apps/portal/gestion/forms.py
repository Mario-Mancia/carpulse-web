from django import forms

from apps.core.imagenes import validar_imagen_subida
from apps.core.models import ClaveRecurso, ConfiguracionPlataforma


class ConfiguracionPlataformaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionPlataforma
        exclude = ("actualizado_en",)
        labels = {
            "nombre_plataforma": "Nombre de la plataforma",
            "correo_contacto": "Correo de contacto",
            "telefono_contacto": "Teléfono de contacto",
            "sitio_web": "Sitio web",
            "max_vehiculos_por_cliente": "Máximo de vehículos por cliente",
            "retencion_sincronizaciones_dias": "Retención de sincronizaciones (días)",
            "recordatorio_anticipacion_dias": "Anticipación de recordatorios (días)",
            "recordatorio_anticipacion_km": "Anticipación de recordatorios (km)",
        }


class RecursoGraficoForm(forms.Form):
    clave = forms.ChoiceField(choices=ClaveRecurso.choices, label="Recurso")
    archivo = forms.ImageField(label="Imagen")
    texto_alternativo = forms.CharField(max_length=150, required=False, label="Texto alternativo")

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        validar_imagen_subida(archivo)
        return archivo


class QuitarRecursoForm(forms.Form):
    clave = forms.ChoiceField(choices=ClaveRecurso.choices)
