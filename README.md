# dynatrace-activegate-extensions
Extensiones ActiveGate (Remote plugin)

Estas extensiones son adecuadas si necesitas monitorear una tecnología donde la instalación del OneAgent no es una opción.

## Instalar el plugin SDK para crear una extensión:
1) Ir a Settings > Monitored technologies > Add new technology monitoring > Add ActiveGate extension, y click en Download Extension SDK.
2) Extraer e instalar: 
```
 pip3 install plugin_sdk-[sdk version number]-py3-none-any.whl
```
3) Crear una extensión. En el directorio donde tenemos los archivos del script y configuración, ejecutar:
```
plugin_sdk build_plugin 
```

Copiar el token en el archivo /opt/dynatrace/remotepluginmodule/agent/conf/plugin_upload.token (Scope: write configuration access)
