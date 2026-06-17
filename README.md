# PolyCrop QGIS Plugin

PolyCrop es un complemento (plugin) para QGIS diseñado para facilitar la implementación de sistemas de policultivos y agroforestería, optimizando el espacio y adaptándose de manera automática a líneas topográficas (como curvas de nivel o keylines).

## Características Principales

- **Diseño Secuencial:** Crea secuencias personalizadas de múltiples cultivos con distintas distancias y cantidades.
- **Espaciado Dinámico:** Respeta la regla del espaciado máximo: al intercalar dos cultivos diferentes, la distancia entre ellos será la del cultivo con mayor requerimiento de espacio.
- **Interfaz Drag & Drop:** Reordena fácilmente tu patrón de plantación arrastrando y soltando los elementos en la tabla.
- **Iconos Personalizables:** Asigna iconos vectoriales (SVG) a cada cultivo para generar mapas altamente gráficos y listos para presentación.
- **Reporte Automático:** Genera un conteo preciso del número total de individuos a plantar de cada especie.
- **Adaptación a Curvas:** Calcula con precisión matemática las distancias sobre geometrías de línea complejas, permitiendo la opción de reiniciar el patrón por cada línea o continuarlo de forma fluida.

## Instalación

1. Descarga el repositorio o la carpeta del plugin `PolyCrop`.
2. Copia la carpeta entera en el directorio de plugins de tu perfil de usuario de QGIS:
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Mac:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. Abre QGIS.
4. Dirígete a **Complementos > Administrar e instalar complementos...**
5. En la pestaña **Instalados**, busca "PolyCrop" y asegúrate de que la casilla esté activada.

## Modo de Uso

1. Carga una capa de **Líneas** en tu proyecto de QGIS (estas pueden representar tus surcos, curvas de nivel o K-lines).
2. Haz clic en el icono de PolyCrop en la barra de herramientas para abrir el panel lateral.
3. En la sección **Capa de Líneas**, selecciona la capa sobre la cual quieres trabajar.
4. En la sección **Patrón de Cultivos**, añade tus cultivos:
   - **Icono:** Elige el símbolo gráfico para el cultivo.
   - **Nombre:** Escribe el nombre de la especie (ej. Aguacate, Maíz).
   - **Espacio (m):** Define la distancia requerida para esta planta.
   - **Cantidad:** Define cuántos individuos de este tipo irán seguidos en la secuencia antes de pasar al siguiente.
5. Usa los botones **Añadir** y **Quitar**, o arrastra las filas para definir tu secuencia.
6. (Opcional) Activa "Invertir dirección de la línea" si tus líneas fueron dibujadas en el sentido contrario a tu flujo de plantación deseado.
7. (Opcional) Activa "Reiniciar patrón por cada línea" si quieres que cada surco comience con el Cultivo #1 de tu lista.
8. Haz clic en **Generar Policultivo**.
9. Se creará una nueva capa de puntos temporal llamada `Policultivo_Generado` con todos los estilos aplicados y se te mostrará un resumen del conteo exacto de individuos por cultivo.

## Añadir Iconos Personalizados

PolyCrop permite utilizar tus propios iconos SVG para representar diferentes especies:

1. Ve a la carpeta de instalación del plugin (ver la sección Instalación).
2. Abre la carpeta `resources/`.
3. Guarda allí tus archivos `.svg` personalizados.
4. La próxima vez que agregues un cultivo a la lista, tus iconos aparecerán automáticamente en el menú desplegable de la columna de Iconos.

## Contribuciones

Las contribuciones son bienvenidas. Si encuentras algún error o tienes una idea para expandir este sistema hacia el análisis de costos o simulación de sombras, ¡siéntete libre de abrir un *Issue* o un *Pull Request*!
