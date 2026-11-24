from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

from apps.core.models import ClaveRecurso, ConfiguracionPlataforma, RecursoGrafico
from apps.core.services import plataforma as servicio
from apps.core.utiles import mensaje_de
from apps.portal.gestion.forms import ConfiguracionPlataformaForm, QuitarRecursoForm, RecursoGraficoForm
from apps.portal.mixins import AdministradorRequeridoMixin, OperadorRequeridoMixin
from apps.usuarios.constants import GRUPO_ADMINISTRADOR


class PanelView(OperadorRequeridoMixin, TemplateView):
    template_name = "gestion/panel.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["es_administrador"] = self.request.user.tiene_algun_rol((GRUPO_ADMINISTRADOR,))
        return contexto


class ConfiguracionView(AdministradorRequeridoMixin, View):
    """Configuración de la plataforma y recursos gráficos (solo Administrator)."""

    template_name = "gestion/configuracion.html"

    def _contexto(self, form=None, form_recurso=None):
        instancia = ConfiguracionPlataforma.objects.first()
        existentes = {r.clave: r for r in RecursoGrafico.objects.all()}
        return {
            "form": form or ConfiguracionPlataformaForm(instance=instancia),
            "form_recurso": form_recurso or RecursoGraficoForm(),
            "recursos_lista": [(clave, etiqueta, existentes.get(clave)) for clave, etiqueta in ClaveRecurso.choices],
        }

    def get(self, request):
        return render(request, self.template_name, self._contexto())

    def post(self, request):
        accion = request.POST.get("accion")
        if accion == "guardar_config":
            return self._guardar_config(request)
        if accion == "subir_recurso":
            return self._subir_recurso(request)
        if accion == "quitar_recurso":
            return self._quitar_recurso(request)
        messages.error(request, "Acción no reconocida.")
        return redirect("gestion:configuracion")

    def _guardar_config(self, request):
        form = ConfiguracionPlataformaForm(request.POST, instance=ConfiguracionPlataforma.objects.first())
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración guardada.")
            return redirect("gestion:configuracion")
        return render(request, self.template_name, self._contexto(form=form), status=400)

    def _subir_recurso(self, request):
        form = RecursoGraficoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                servicio.asignar_recurso(
                    form.cleaned_data["clave"],
                    form.cleaned_data["archivo"],
                    usuario=request.user,
                    texto_alternativo=form.cleaned_data["texto_alternativo"],
                )
            except ValidationError as error:
                form.add_error("archivo", mensaje_de(error))
            else:
                messages.success(request, "Recurso gráfico actualizado.")
                return redirect("gestion:configuracion")
        return render(request, self.template_name, self._contexto(form_recurso=form), status=400)

    def _quitar_recurso(self, request):
        form = QuitarRecursoForm(request.POST)
        if form.is_valid() and servicio.quitar_recurso(form.cleaned_data["clave"]):
            messages.success(request, "Recurso gráfico eliminado.")
        else:
            messages.error(request, "No se pudo eliminar el recurso indicado.")
        return redirect("gestion:configuracion")
