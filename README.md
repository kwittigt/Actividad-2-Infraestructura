# INFB6074 – Actividad Semana 2: Benchmarking de Jerarquía de Memoria e I/O

**Universidad Tecnológica Metropolitana (UTEM)** Ingeniería Civil en Ciencia de Datos  
Profesor: Dr. Ing. Michael Miranda Sandoval | Estudiante: Koen Wittig Toro  
Abril 2026


---

## Descripción

Este proyecto implementa un estudio experimental comparativo de **cuatro aspectos críticos en la infraestructura de datos**:

1. **Jerarquía de Memoria**: Impacto del acceso en RAM vs. almacenamiento secundario (disco).
2. **Patrones de Acceso**: Diferencias de rendimiento entre lectura secuencial y aleatoria.
3. **Cuellos de Botella**: Identificación de latencias en pipelines ETL (Ingesta, Transformación y Almacenamiento).
4. **Arquitecturas de Procesamiento**: Evaluación de los *trade-offs* de latencia y *throughput* entre modelos *batch* y *streaming*.

Los experimentos están diseñados para cuantificar cómo estas decisiones arquitectónicas afectan la eficiencia en cargas de trabajo típicas de Ciencia de Datos.

---

## Estructura del Repositorio

```text
actividad2/
├── experiments.py              # Código principal de los 4 experimentos (A, B, C, D)
├── README.md                   # Este archivo de documentación
├── data/                       # Directorio temporal para los artefactos de datos (CSV, Parquet, binarios)
├── results/                    # Directorio persistente para tablas de métricas
├── visualizations/             # Directorio de gráficos exportados (PNG)          
└── Informe_Actividad2
