# 📧 Configuración de Correo para Railway.app

## 🚨 **Problema Común**
Railway.app puede bloquear conexiones SMTP salientes o las credenciales pueden no estar configuradas correctamente como variables de entorno.

## ✅ **Soluciones Implementadas**

### **1. Variables de Entorno (Recomendada)**

En tu dashboard de Railway.app, ve a tu proyecto → Variables → Agregar las siguientes:

```bash
# Configuración básica de Gmail
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=soporte.laplayita@gmail.com
EMAIL_HOST_PASSWORD=mafqcymwowaxzvdb
DEFAULT_FROM_EMAIL=soporte.laplayita@gmail.com
EMAIL_TIMEOUT=30
```

### **2. Proveedores Alternativos**

#### **SendGrid (Recomendado para producción)**
```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=tu_api_key_de_sendgrid
```

#### **Mailgun**
```bash
EMAIL_PROVIDER=mailgun
MAILGUN_SMTP_LOGIN=tu_login_mailgun
MAILGUN_SMTP_PASSWORD=tu_password_mailgun
```

#### **Outlook/Hotmail**
```bash
EMAIL_PROVIDER=outlook
EMAIL_HOST_USER=tu_email@outlook.com
EMAIL_HOST_PASSWORD=tu_password_outlook
```

## 🔧 **Configuración Paso a Paso**

### **Opción 1: Gmail (Actual)**

1. **Mantener configuración actual** (ya está en el código)
2. **Verificar que Gmail permita aplicaciones menos seguras**
3. **Usar contraseña de aplicación** si tienes 2FA activado

### **Opción 2: SendGrid (Recomendada)**

1. **Crear cuenta en SendGrid** (100 correos gratis/día)
2. **Obtener API Key** desde el dashboard
3. **Configurar variables en Railway:**
   ```bash
   EMAIL_PROVIDER=sendgrid
   SENDGRID_API_KEY=SG.xxxxxxxxxx
   ```

### **Opción 3: Mailgun**

1. **Crear cuenta en Mailgun** (5,000 correos gratis/mes)
2. **Verificar dominio** (opcional, puedes usar sandbox)
3. **Configurar variables en Railway:**
   ```bash
   EMAIL_PROVIDER=mailgun
   MAILGUN_SMTP_LOGIN=postmaster@sandbox-xxx.mailgun.org
   MAILGUN_SMTP_PASSWORD=tu_password_mailgun
   ```

## 🧪 **Probar Configuración**

### **1. Desde la aplicación:**
Visita: `https://tu-app.railway.app/pos/test-email/`

### **2. Enviar correo de prueba:**
```bash
curl -X POST https://tu-app.railway.app/pos/test-email/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "test_email=tu_email@gmail.com"
```

### **3. Revisar logs en Railway:**
Ve a tu proyecto → Deployments → Ver logs para errores de correo

## 🔍 **Diagnóstico de Problemas**

### **Error: Connection refused**
- **Causa:** Railway bloquea puerto SMTP
- **Solución:** Usar SendGrid o Mailgun API

### **Error: Authentication failed**
- **Causa:** Credenciales incorrectas
- **Solución:** Verificar variables de entorno

### **Error: Timeout**
- **Causa:** Conexión lenta
- **Solución:** Aumentar `EMAIL_TIMEOUT=60`

## 📋 **Checklist de Configuración**

- [ ] Variables de entorno configuradas en Railway
- [ ] Proveedor de correo seleccionado
- [ ] Credenciales válidas
- [ ] Prueba de envío exitosa
- [ ] Logs sin errores

## 🚀 **Configuración Recomendada para Producción**

```bash
# SendGrid (Más confiable)
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.tu_api_key_real
DEFAULT_FROM_EMAIL=noreply@tudominio.com
EMAIL_TIMEOUT=30

# O Mailgun
EMAIL_PROVIDER=mailgun
MAILGUN_SMTP_LOGIN=postmaster@mg.tudominio.com
MAILGUN_SMTP_PASSWORD=tu_password_real
DEFAULT_FROM_EMAIL=noreply@tudominio.com
EMAIL_TIMEOUT=30
```

## 🔧 **Funcionalidades Implementadas**

1. **Manejo de errores robusto** - Fallbacks automáticos
2. **Múltiples proveedores** - Gmail, SendGrid, Mailgun, Outlook
3. **Logging detallado** - Para debugging
4. **Pruebas integradas** - Endpoint de testing
5. **Templates mejorados** - HTML responsive para correos
6. **Configuración flexible** - Variables de entorno

## 📞 **Soporte**

Si sigues teniendo problemas:

1. **Revisa los logs** en Railway
2. **Prueba la configuración** con el endpoint de testing
3. **Verifica las variables** de entorno
4. **Considera cambiar** a SendGrid o Mailgun

---

**¡Con esta configuración, el correo debería funcionar perfectamente en Railway.app!** 🎉