# Edición diaria de Kastigo en GitHub Actions

El flujo `Actualizar Kastigo` trabaja únicamente en `Matisandev/kastigo`, rama `main`. Se programa a las 09:00 en `America/Santiago` y admite ejecución manual desde el navegador del celular: Actions → Actualizar Kastigo → Run workflow.

## Activación

1. En Settings → Secrets and variables → Actions del repositorio Kastigo, crear el secreto `OPENAI_API_KEY` con una clave de un proyecto de OpenAI dedicado a Kastigo. No pegarla en chats, archivos del repositorio o registros. Configurar facturación y alertas de presupuesto en OpenAI por separado; una alerta no es necesariamente un límite duro.
2. Ejecutar manualmente dejando activada la opción **Solo comprobar instalación**. No usa IA, no crea la marca diaria y no publica. Revisa los resultados.
3. Antes de activar la nube, pausar la automatización local de Kastigo para que no haya dos sistemas actualizando.
4. Crear la variable de repositorio `KASTIGO_ENABLED` con valor `true`. Luego ejecutar manualmente desmarcando **Solo comprobar instalación**. Esta ejecución sí consume API. Revisar el primer resultado y sus tokens; no hay estimación de coste mensual validada antes de esa prueba.
5. Para desactivar la investigación sin borrar archivos, quitar la variable o ponerla en `false`. La tarea comprobará el código, pero no llamará a OpenAI ni publicará.

El acceso temporal `GITHUB_TOKEN` de Actions se limita al repositorio y tiene Contents: write (actualización y marca diaria) y Pages: write (solicitar despliegue). No se copia la credencial local. La credencial que instale el archivo de flujo necesita permiso Workflows: write además de Contents: write; esto no autoriza ampliar acceso a otros repositorios.

## Controles

- Máximo un intento editorial por fecha de Santiago, compartido entre horario y botón manual. Una referencia Git inmutable `kastigo-daily-AAAA-MM-DD` se crea antes de consumir IA. Una ejecución sin novedades o fallida también consume ese intento; no se elimina automáticamente.
- Grupo de concurrencia único, sin cancelar una edición en curso. No se fuerza ninguna escritura. Se verifica la rama vigente y el SHA de index.html antes de publicar.
- Tres llamadas máximas a la API Responses, modelo `gpt-5.4`: investigación con hasta 24 llamadas web; propuesta de cambios; revisión editorial y visual. Cada llamada admite hasta 12.000 tokens de salida y no se reintenta automáticamente. El consumo real se informa en el resumen. No se usan herramientas de ejecución de código del modelo.
- La investigación debe abrir fuentes, no solo buscar. Cada cambio debe referenciar una URL abierta. Se conserva el HTML fuera de los tres JSON, estructura, textos fijos, tipos y equivalencia numérica. El revisor rechaza investigaciones incompletas, datos sin fuente y traducciones inconsistentes. Estos controles reducen errores, pero no garantizan exactitud editorial absoluta.
- Se prueba la página en tres idiomas, móvil y escritorio; se revisan seis capturas con el modelo. Si falla cualquier etapa, no se envía el contenido.
- Sin novedades, no se cambia la fecha. Los días no ejecutados no generan ediciones retroactivas.
- Tras enviar index.html, se solicita explícitamente un build de Pages y se compara la respuesta pública exacta durante hasta diez minutos. Los estados «enviado» y «publicación verificada» son distintos. Si falla el despliegue, se informa sin sobrescribir de nuevo.
- GitHub puede retrasar el horario. En repositorios públicos también puede desactivar horarios por inactividad prolongada; revisar ocasionalmente Actions.

## Pruebas

`python3 -m unittest discover -s tests -v`

`npm ci --ignore-scripts` y `npx playwright install --with-deps chromium` preparan las comprobaciones de navegador en Linux. El flujo contiene un modo de comprobación sin IA ni publicación.

La migración no cambia la estructura ni el diseño de la página. El texto fijo que anuncia actualizaciones cada dos horas todavía pertenece a la interfaz original; cambiarlo requiere una modificación de interfaz separada.
