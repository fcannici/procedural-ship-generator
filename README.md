# Procedural Ship Generator (Blender Addon)

Este addon para Blender 3.0+ permite generar barcos modulares paramétricos ideales para impresión 3D (FDM) y partidas de rol (D&D, Pathfinder, etc.). 

## Características Principales

- **Arquitectura Modular:** Genera piezas separadas (Proa, Centro, Popa) que se ensamblan físicamente.
- **Paramétrico en Tiempo Real:** Modifique el largo, el ancho, la altura de las paredes y el grosor del suelo con retroalimentación visual instantánea.
- **Sincronización Inteligente (Smart Sync):** Al cambiar las proporciones de una pieza, todo el barco se ajusta y realinea automáticamente para mantenerse en perfecta armonía sin colisiones.
- **Cuadrícula Integrada:** Genera automáticamente una cuadrícula esculpida (1 pulgada / 25.4mm) en el suelo para miniaturas.
- **Arquitectura Multinivel (Castillos):** Eleve la cubierta de la Proa o la Popa para crear castillos de mando con escaleras integradas, listas para imprimir.
- **Clips de Unión (Dovetail):** Incluye canales pre-cortados y un generador de clips de unión con tolerancias ajustables para ensamblar las piezas firmemente.
- **Cubiertas Superiores Removibles:** Genera las tapas de la cubierta principal que encastran en el casco.

## Instalación

1. Descargue el archivo `procedural_ship_generator.zip`.
2. En Blender, vaya a `Edit` > `Preferences` > `Add-ons`.
3. Haga clic en `Install...` y seleccione el archivo `.zip`.
4. Active la casilla junto a **"Mesh: Procedural Ship Generator"**.

## Tutorial de Uso Rápido

### 1. Generar el Barco Base
1. Presione `N` en la vista 3D para abrir el panel lateral y busque la pestaña **"Procedural Ship"**.
2. Haga clic en el botón **"Generar Barco Completo"**. Esto creará la Proa, el Centro y la Popa ya alineados.

### 2. Ajustar Proporciones
1. Seleccione cualquiera de las secciones del barco (por ejemplo, el Centro).
2. En el panel, cambie el **"Largo (Casillas)"** o el **"Ancho interno"**.
3. Verá cómo **todas las secciones** se escalan al unísono y se empujan entre sí para no chocar (Smart Sync).

### 3. Crear Castillos de Popa/Proa
1. Seleccione la sección de Popa.
2. En la sección **"Arquitectura Multinivel"**, active **"Castillo de Popa"**.
3. Verá cómo la cubierta trasera se eleva y aparecen escaleras frontales. Puede ajustar la "Elevación" en milímetros a su gusto.

### 4. Generar Clips de Unión
1. Cuando esté listo para imprimir, haga clic en el botón **"Generar Clip de Unión"**.
2. Esto creará un clip "Dovetail" en el centro de la escena.
3. Puede ajustar la "Tolerancia FDM" en el panel para hacer el encastre más apretado o más suelto según la precisión de su impresora 3D.

### 5. Impresión 3D
- Seleccione cada parte por separado (Centro, Popa, Proa, Clip, Tapas) y expórtelas como archivos `.STL` (`File` > `Export` > `Stl`).
- El modelo está diseñado para imprimirse sin soportes en la mayoría de sus partes (los canales de los clips están orientados horizontalmente y pueden requerir puentes cortos).

## Autor
Creado con asistencia de J.A.R.V.I.S.
