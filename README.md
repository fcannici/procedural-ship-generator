# Procedural Ship Generator (Blender Addon)

Este addon para Blender 3.0+ permite generar barcos modulares paramétricos ideales para impresión 3D (FDM) y partidas de rol (D&D, Pathfinder, etc.). 

## Características Principales

- **Arquitectura Modular:** Genera piezas separadas (Proa, Centro, Popa) que se ensamblan físicamente.
- **Paramétrico en Tiempo Real:** Modifique el largo, el ancho, la altura de las paredes y el grosor del suelo con retroalimentación visual instantánea.
- **Sincronización Inteligente (Smart Sync):** Al cambiar las proporciones de una pieza, todo el barco se ajusta y realinea automáticamente para mantenerse en perfecta armonía sin colisiones.
- **Generación Limpia:** Al agregar nuevas secciones sueltas, el sistema genera mallas 100% vírgenes sin heredar propiedades de otros objetos, garantizando que no se arrastren escaleras ni parámetros no deseados.
- **Cuadrícula Integrada:** Genera automáticamente una cuadrícula esculpida (1 pulgada / 25.4mm) en el suelo para miniaturas.
- **Escaleras Independientes y Accesorios Modulares:** Añada múltiples escaleras (generadas como objetos _Escaleras independientes) y accesorios. Use **Shift+Clic** para clonarlos invirtiendo automáticamente su posición (espejado rápido).
- **Arquitectura Multinivel (Castillos):** Eleve la cubierta de la Proa o la Popa para crear castillos de mando con escaleras integradas, listas para imprimir.
- **Escala por Raza Creadora:** Escala las alturas de las paredes y proporciones arquitectónicas automáticamente para medianos, humanos, gigantes o titanes (sin desfasar la cuadrícula táctica).
- **Compartimentación Inferior:** Divida la bodega (nivel inferior) en múltiples habitaciones cerrando sus caras frontales paramétricamente.
- **Clips de Unión (Dovetail):** Incluye canales pre-cortados y un generador de clips de unión con tolerancias ajustables para ensamblar las piezas firmemente.
- **Cubiertas Removibles:** Genera las tapas de la cubierta principal como objetos separados, dejando el casco como una bañera hueca para acceder a los niveles inferiores.

## Instalación

1. Descargue el archivo procedural_ship_generator.zip.
2. En Blender, vaya a Edit > Preferences > Add-ons.
3. Haga clic en Install... y seleccione el archivo .zip.
4. Active la casilla junto a **"Mesh: Procedural Ship Generator"**.

## Tutorial de Uso Rápido

### 1. Generar el Barco Base
1. Presione N en la vista 3D para abrir el panel lateral y busque la pestaña **"Procedural Ship"**.
2. En la sección **"Configuración Inicial"**, seleccione la **"Raza Creadora por defecto"** (esto definirá la escala de todas las paredes).
3. Haga clic en el botón **"Generar Barco Completo (3 Partes)"**. Esto creará la Proa, el Centro y la Popa ya alineados.

### 2. Ajustar Proporciones
1. Seleccione cualquiera de las secciones del barco (por ejemplo, el Centro).
2. En el panel, cambie el **"Largo (Casillas)"** o el **"Ancho interno"**.
3. Verá cómo **todas las secciones** se escalan al unísono y se empujan entre sí para no chocar (Smart Sync).

### 3. Modificaciones Procedurales vs Manuales (¡Importante!)
Este addon es **100% procedural**. Esto significa que cada vez que usted mueve una perilla o marca un botón en el panel lateral, el addon **borra por completo el objeto y lo reconstruye desde cero**.
- **Regla de Oro:** NUNCA modifique el barco entrando a "Edit Mode" (por ejemplo, para borrar una cara o hacer un agujero a mano). En cuanto cambie un parámetro en el panel, ¡sus cambios manuales se borrarán!
- **Para hacer un barco destapado (sin piso de cubierta principal):** No borre el piso a mano. Simplemente active la opción **"Cubierta Removible"**. Esto generará la cubierta como una pieza separada; una vez generada, puede ocultarla o borrarla, y el barco "recordará" que debe reconstruirse destapado.

### 4. Compartimentación y Castillos
- **Castillos:** Seleccione la Popa/Proa, active "Castillo de Popa/Proa". Esto eleva la cubierta trasera/delantera.
- **Habitaciones de Bodega:** Si el barco no tiene cubierta removible (está destapado), active **"Cerrar Bodega Frontal"** en la sección "Arquitectura Multinivel" para crear una pared interna divisoria (Bulkhead) que separe la bodega de una pieza con la pieza adyacente.

### 5. Configurar Escaleras Interiores
1. Seleccione una sección y haga clic en **"Añadir Escalera"**.
2. Ajuste el largo, ancho, nivel y orientación (Offset X/Y) para colocarla donde desee. El agujero en el piso se tallará automáticamente.
3. **Atajo de Simetría:** Si desea colocar otra escalera idéntica del lado opuesto, haga **Shift + Clic** en "Añadir Escalera". Esto clonará la escalera y multiplicará su posición X por -1, ubicándola perfectamente simétrica.

### 6. Accesorios Modulares
1. Vaya a la sección **"Accesorios Modulares"** y pulse **"Añadir Accesorio"**. Al igual que las escaleras, usar **Shift+Clic** lo duplicará del lado opuesto.
2. Elija el tipo (Timón, Mástil Mayor, Bauprés, etc.) y ajústelo sobre la cubierta. Se generará automáticamente un agujero de encastre (snap joint) en el barco (compatible universalmente a 3mm).
3. Para imprimir el accesorio de forma independiente, pulse **"Extraer Modelo Base (Independiente)"**. Se creará un nuevo objeto suelto listo para exportar.

### 7. Configurar Tolerancias FDM y Clips de Unión
1. Cuando esté listo para imprimir, genere el clip haciendo clic en **"Generar Clip de Unión"**.
2. En la sección **"Impresión FDM"**, ajuste la **"Tolerancia FDM (mm)"** (afecta la holgura general de los clips).
3. Si los pisos de la cubierta superior (los removibles) quedan muy sueltos o apretados al imprimir, use el parámetro **"Compensación Ancho Cubierta (mm)"**. Valores positivos (ej. 1.5) ensancharán la madera, logrando un *click* perfecto según la contracción de su filamento.

## Autor
Creado con asistencia de J.A.R.V.I.S.

