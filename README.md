CREDENCIALES PARA INICIAR:
CORREO: carlos@careguardian.com
CONTRASEÑA: CareGuardian123

# CareGuardian 🩺
## Sistema inteligente de acompañamiento y seguimiento para adultos mayores

**CareGuardian** es una plataforma web orientada al acompañamiento y cuidado de adultos mayores. Su propósito es facilitar el trabajo de familiares y cuidadores mediante herramientas digitales para administrar información, realizar seguimiento de síntomas, organizar medicamentos y citas médicas y analizar la evolución de los pacientes mediante inteligencia artificial.

El proyecto integra tecnologías de desarrollo web, almacenamiento de información, procesamiento de datos e inteligencia artificial, buscando ofrecer una solución centralizada, modular y escalable.

---

# 1. Objetivo general

Desarrollar una plataforma web que facilite el acompañamiento y seguimiento de adultos mayores mediante la gestión de información personal, registros de síntomas, actividades de cuidado y análisis inteligente de patrones de evolución.

## Objetivos específicos

- Centralizar la información de los adultos mayores.
- Facilitar el seguimiento de medicamentos y citas médicas.
- Registrar síntomas y cambios en el estado del paciente.
- Mantener un historial de seguimiento.
- Incorporar inteligencia artificial para analizar patrones en la información registrada.
- Generar información de apoyo para familiares y cuidadores.
- Implementar diferentes estrategias de renderizado web para mejorar la experiencia y el funcionamiento de la aplicación.

---

# 2. Tecnologías utilizadas

El proyecto utiliza una arquitectura cliente-servidor con separación entre frontend, backend y base de datos.

## 2.1. Frontend

| Tecnología | Función |
|---|---|
| Angular 22 | Framework para desarrollar la interfaz web. |
| TypeScript | Lenguaje principal del frontend. |
| HTML5 | Estructura de los componentes y páginas. |
| CSS3 | Diseño y presentación visual. |
| Node.js | Entorno de ejecución utilizado para las herramientas del frontend y SSR. |

El frontend permite a los usuarios interactuar con los módulos del sistema, consultar información y realizar operaciones mediante una interfaz organizada por componentes.

También se trabaja con renderizado del lado del servidor (SSR), además del funcionamiento habitual del navegador.

## 2.2. Backend

| Tecnología | Función |
|---|---|
| Python | Lenguaje principal del backend. |
| FastAPI | Framework para desarrollar la API REST. |
| SQLAlchemy | Comunicación con la base de datos mediante ORM. |
| Pydantic | Validación y estructuración de datos. |
| Alembic | Administración de migraciones de PostgreSQL. |
| HTTPX | Cliente HTTP utilizado para comunicarse con Groq. |

El backend recibe las solicitudes del frontend, valida los datos, ejecuta la lógica de negocio y administra las operaciones relacionadas con la información almacenada.

## 2.3. Base de datos

**PostgreSQL**

Se utiliza para almacenar de forma persistente la información del sistema.

La comunicación con la base de datos se realiza mediante SQLAlchemy, mientras que Alembic permite administrar los cambios en su estructura mediante migraciones.

## 2.4. Inteligencia artificial

**Groq API**

Se integró Groq como proveedor de inteligencia artificial para incorporar capacidades de análisis de información.

| Elemento | Configuración |
|---|---|
| Proveedor | Groq |
| Modelo | `openai/gpt-oss-20b` |
| Comunicación | HTTP mediante HTTPX |
| Configuración | Variables de entorno |
| Módulo | `app/services/groq_analysis.py` |

La integración permite enviar información al modelo para procesarla y obtener respuestas estructuradas que pueden utilizarse en el análisis de evolución de los pacientes.

La API key se administra exclusivamente desde el backend mediante la variable de entorno `GROQ_API_KEY`.

El frontend no necesita conocer ni almacenar esta clave.

---

# 3. Integración de inteligencia artificial con Groq

Uno de los componentes importantes de CareGuardian es la incorporación de inteligencia artificial mediante Groq.

Esta integración permite ampliar las capacidades del sistema para analizar información relacionada con el seguimiento de los adultos mayores.

## ¿Cómo funciona?

1. El cuidador registra información relacionada con el paciente.
2. El backend recibe y organiza los datos.
3. El módulo de análisis prepara la información que será procesada.
4. El backend realiza una solicitud a Groq mediante HTTPX.
5. Groq procesa la solicitud utilizando el modelo configurado.
6. El resultado es recibido por el backend.
7. La aplicación puede utilizar la respuesta para presentar información de análisis y seguimiento.

## Modelo utilizado

`openai/gpt-oss-20b`

Este modelo se configura mediante la variable:

```env
GROQ_MODEL=openai/gpt-oss-20b
```

La clave de acceso se configura mediante:

```env
GROQ_API_KEY=tu_clave_de_groq
```

La comunicación se realiza desde el servidor, evitando exponer las credenciales en el navegador.

## Validación de la integración

La conexión con Groq fue probada satisfactoriamente.

Se verificó:

- Disponibilidad del modelo.
- Comunicación con la API.
- Respuesta HTTP 200.
- Generación de una respuesta de prueba con estado `ok`.

## Aplicación dentro del proyecto

La inteligencia artificial funciona como herramienta de apoyo para el análisis de información.

Puede contribuir a identificar tendencias, cambios y patrones presentes en los registros del paciente.

**Importante:** los resultados son orientativos y no sustituyen la evaluación, el diagnóstico ni las decisiones de profesionales de la salud.

---

# 4. Patrones de renderizado web (Rendering Patterns)

Otro aspecto técnico trabajado en CareGuardian es el estudio y aplicación de estrategias de renderizado web.

Los patrones de renderizado determinan cómo y dónde se genera el contenido que finalmente recibe el navegador.

En el proyecto se trabaja con los enfoques de renderizado del lado del cliente y del servidor, especialmente relacionados con Angular y su configuración SSR.

## 4.1. CSR (Client-Side Rendering)

El renderizado del lado del cliente consiste en entregar inicialmente una estructura HTML básica y permitir que JavaScript genere el contenido de la aplicación dentro del navegador.

**Funcionamiento:**

1. El navegador solicita la aplicación.
2. Recibe el HTML inicial y los archivos JavaScript.
3. Angular se ejecuta en el navegador.
4. Se construyen los componentes.
5. Se muestra la interfaz al usuario.

**Ventajas:**
- Permite interfaces interactivas.
- Facilita la actualización dinámica de componentes.
- Es adecuado para aplicaciones con paneles y operaciones frecuentes.

**Aplicación en CareGuardian:**

Se utiliza el funcionamiento habitual de Angular en el navegador para permitir la interacción con los módulos de la plataforma.

## 4.2. SSR (Server-Side Rendering)

El renderizado del lado del servidor permite generar el HTML inicial antes de enviarlo al navegador.

**Funcionamiento:**

1. El navegador solicita una página.
2. El servidor ejecuta el proceso de renderizado.
3. Se genera el HTML inicial.
4. El navegador recibe el contenido renderizado.
5. Angular se inicializa en el cliente para habilitar la interactividad.

**Ventajas:**
- Permite mostrar contenido inicial desde el servidor.
- Puede mejorar la percepción de velocidad de carga.
- Facilita la indexación de contenido público por buscadores.
- Puede mejorar la experiencia en la primera visualización.

**Aplicación en CareGuardian:**

El proyecto incorpora Angular con configuración SSR y Node.js para soportar el renderizado del lado del servidor.

## 4.3. SSG (Static Site Generation)

SSG consiste en generar páginas HTML estáticas durante el proceso de construcción de la aplicación.

El contenido se prepara antes de que el usuario realice una solicitud.

**Ventajas:**
- Permite servir archivos estáticos rápidamente.
- Reduce el trabajo de procesamiento por solicitud.
- Es útil para páginas cuyo contenido cambia poco.

SSG se documenta como una estrategia de renderizado relacionada, pero no se afirma como una funcionalidad implementada en la versión desplegada de CareGuardian.

## 4.4. ISR (Incremental Static Regeneration)

ISR permite actualizar páginas estáticas después de su generación inicial, siguiendo una estrategia de regeneración definida.

**Ventajas:**
- Permite reutilizar contenido estático.
- Facilita la actualización periódica de páginas.
- Reduce la necesidad de reconstruir todo el sitio ante ciertos cambios.

ISR también se incluye como concepto de arquitectura web, no como una funcionalidad confirmada en la implementación actual.

## Comparación de patrones

| Patrón | Lugar de renderizado | Momento |
|---|---|---|
| CSR | Navegador | Durante la ejecución del cliente |
| SSR | Servidor | Durante la solicitud |
| SSG | Proceso de construcción | Antes de la solicitud |
| ISR | Generación estática con regeneración | Después de la generación inicial |

---

# 5. Arquitectura general

CareGuardian utiliza una arquitectura dividida en componentes independientes.

### Frontend

Desarrollado con Angular 22. Se encarga de presentar la información y permitir la interacción con los usuarios.

### Backend

Desarrollado con FastAPI. Administra la lógica de negocio, recibe solicitudes, valida datos y realiza operaciones con PostgreSQL.

### Base de datos

PostgreSQL almacena la información persistente del sistema.

### Inteligencia artificial

Groq se integra mediante el backend para procesar solicitudes de análisis utilizando el modelo `openai/gpt-oss-20b`.

### Flujo general

```text
             USUARIO
                |
                v
       ANGULAR 22 FRONTEND
                |
                v
           API REST
            FASTAPI
                |
       +--------+--------+
       |                 |
       v                 v
  POSTGRESQL          GROQ API
       |                 |
       v                 v
  INFORMACIÓN       ANÁLISIS IA
       |                 |
       +--------+--------+
                |
                v
         RESPUESTA API
                |
                v
        INTERFAZ ANGULAR
```

---

# 6. Funcionamiento de los módulos

## 6.1. Gestión de usuarios

Permite administrar la información de los usuarios que interactúan con la plataforma.

El backend recibe los datos, realiza las validaciones correspondientes y ejecuta las operaciones de almacenamiento.

## 6.2. Gestión de pacientes

Permite centralizar la información de los adultos mayores para facilitar su consulta y seguimiento.

## 6.3. Control de medicamentos

Organiza información relacionada con medicamentos, horarios y seguimiento de su administración.

## 6.4. Calendario de citas médicas

Permite organizar las citas y actividades relacionadas con la atención médica de los pacientes.

## 6.5. Registro de síntomas

Permite almacenar observaciones relacionadas con el estado del paciente.

Estos registros pueden servir como fuente de información para el seguimiento y el análisis de evolución.

## 6.6. Análisis de evolución mediante IA

Utiliza los registros disponibles para apoyar el análisis de patrones y cambios en la evolución del adulto mayor.

El componente de Groq amplía las capacidades de procesamiento y generación de respuestas del sistema.

---

# 7. Funcionamiento técnico de una solicitud

El proceso de comunicación entre los componentes funciona de la siguiente manera:

1. El usuario realiza una acción desde Angular.
2. El frontend construye una solicitud HTTP.
3. FastAPI recibe la petición.
4. Pydantic valida los datos recibidos.
5. El backend ejecuta la lógica correspondiente.
6. SQLAlchemy realiza las operaciones necesarias en PostgreSQL.
7. Si la operación requiere análisis inteligente, el backend utiliza el módulo de Groq.
8. La respuesta es procesada por FastAPI.
9. Angular recibe la información y actualiza la interfaz.

Esta separación permite mantener una arquitectura organizada y facilita el mantenimiento del proyecto.

---

# 8. Despliegue e infraestructura

CareGuardian utiliza Railway como plataforma de despliegue.

Los componentes principales de producción son:

- Backend desarrollado con FastAPI.
- Frontend desarrollado con Angular y configuración SSR.
- Base de datos PostgreSQL.
- Integración externa con Groq.

También se utiliza Docker para preparar los entornos de ejecución y facilitar la construcción y despliegue de los servicios.

Los repositorios se administran mediante Git y GitHub.

## Variables de entorno

La configuración de producción utiliza variables de entorno para evitar almacenar credenciales directamente en el código.

Entre las variables utilizadas se encuentran:

```env
DATABASE_URL=
SECRET_KEY=
CORS_ORIGINS=
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
API_BASE_URL=
PUBLIC_ORIGIN=
```

Los valores reales deben configurarse en el entorno correspondiente y nunca publicarse en GitHub.

---

# 9. Pruebas y validaciones

El proyecto cuenta con pruebas automatizadas para verificar el funcionamiento del backend.

Se registró un resultado de:

**32 pruebas aprobadas.**

También se realizaron validaciones de la integración con Groq, incluyendo la comunicación con el modelo y la recepción de respuestas satisfactorias.

Las pruebas permiten detectar errores y comprobar que los componentes principales se comporten según lo esperado.

---

# 10. Herramientas de desarrollo

| Herramienta | Uso |
|---|---|
| Visual Studio Code | Desarrollo y edición del código. |
| Python | Desarrollo del backend. |
| Angular CLI | Administración y ejecución del frontend. |
| Node.js | Entorno de ejecución de Angular y SSR. |
| FastAPI | Construcción de servicios web. |
| PostgreSQL | Persistencia de información. |
| SQLAlchemy | Acceso a datos. |
| Alembic | Migraciones de base de datos. |
| Groq | Procesamiento mediante inteligencia artificial. |
| HTTPX | Comunicación HTTP con Groq. |
| Docker | Contenerización. |
| Railway | Despliegue de servicios. |
| Git y GitHub | Control de versiones y repositorios. |

---

# 11. Seguridad y buenas prácticas

CareGuardian contempla buenas prácticas de desarrollo:

- Separación entre frontend y backend.
- Validación de datos mediante Pydantic.
- Uso de variables de entorno para información sensible.
- Protección de las credenciales de Groq.
- Configuración de CORS.
- Control de cambios en la base de datos mediante Alembic.
- Separación de entornos de desarrollo y producción.
- Comunicación entre servicios mediante API REST.

Por tratarse de información relacionada con adultos mayores, es importante mantener controles de acceso y proteger los datos personales y de salud.

---

# 12. Posibles mejoras y evolución

El proyecto puede ampliarse mediante nuevas funcionalidades:

- Mayor precisión en el análisis de evolución.
- Ampliación del historial de síntomas.
- Mejoras en la generación de informes.
- Incorporación de notificaciones y recordatorios.
- Mejoras en la gestión de medicamentos y citas.
- Ampliación de las pruebas automatizadas.
- Optimización de los procesos de renderizado.
- Fortalecimiento de la seguridad y protección de datos.

---

# 13. Conclusión

CareGuardian integra desarrollo web, gestión de bases de datos e inteligencia artificial para ofrecer una herramienta tecnológica orientada al acompañamiento de adultos mayores.

La combinación de Angular 22, FastAPI y PostgreSQL proporciona una arquitectura modular, mientras que la integración con Groq incorpora capacidades de análisis inteligente.

Adicionalmente, el trabajo con patrones de renderizado web permite comprender y utilizar diferentes estrategias para generar y entregar contenido al navegador, incluyendo CSR y SSR.

El proyecto busca facilitar la labor de los cuidadores, centralizar información relevante y contribuir a un seguimiento más organizado de los adultos mayores.

---

**CareGuardian**

*Tecnología, inteligencia y acompañamiento para mejorar el cuidado de los adultos mayores.*
