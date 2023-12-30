from django.db import models
from django.http import request
# Create your models here.
class PayType(models.Model):
    pay_id = models.AutoField(primary_key=True)
    pay_name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'Pay_type'

    def __str__(self):
        return self.pay_name
    

class Providers(models.Model):
    prov_id = models.AutoField(primary_key=True)
    prov_name = models.CharField(max_length=255)
    prov_dni = models.CharField(max_length=20)
    prov_phone = models.CharField(max_length=20)
    prov_email = models.EmailField()
    prov_city = models.CharField(max_length=100)
    prov_status = models.CharField(max_length=50)
    prov_type = models.CharField(max_length=50)
    prov_address = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'Providers'

    def __str__(self):
        return self.prov_name
    
    def save(self, *args, user_id=None, **kwargs):
        action_type = 'CREATE' if not self.pk else 'UPDATE'
        super().save(*args, **kwargs)
        self.audit_log(action_type, user_id)

    def delete(self, *args, user_id=None, **kwargs):
        super().delete(*args, **kwargs)
        self.audit_log('DELETE', user_id)

    def audit_log(self, action_type, user_id=None):
        from django.db import connection

        ip_address = '127.0.0.1'  # Puedes obtener esto de la solicitud si es necesario
        table_name = 'Providers'
        description = f"{action_type} - Provider: {self.prov_name}"
        
        # Mapeo de action_type a functionName
        function_mapping = {
            'CREATE': 'function-2',  # Crear
            'UPDATE': 'function-3',  # Editar
            'DELETE': 'function-4',  # Eliminar
        }
        
        function_name = function_mapping.get(action_type, 'function-1')  # Iniciar sesión por defecto
        observation = 'Nada'

        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO audit_log (action_type, table_name, row_id, user_id, ip_address, description, function_name, observation) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                [action_type, table_name, self.pk, user_id, ip_address, description, function_name, observation]
            )
    
    def get_prov_type_display(self):
        prov_type_int = int(self.prov_type)  # Convertir a entero
        if prov_type_int == 1:
            return "Crédito"
        elif prov_type_int == 2:
            return "Contado"
        else:
            return str(prov_type_int)
    
    
    def get_prov_type_display(self):
        prov_type_int = int(self.prov_type)  # Convertir a entero
        if prov_type_int == 1:
            return "Crédito"
        elif prov_type_int == 2:
            return "Contado"
        else:
            return str(prov_type_int)



class Invoice(models.Model):
    invo_id = models.AutoField(primary_key=True)
    invo_date = models.DateField()
    user_id = models.IntegerField()  # Ajusta según tus necesidades
    expedition_date = models.DateField()
    invo_prov = models.ForeignKey(Providers, on_delete=models.CASCADE)
    invo_pay_type = models.ForeignKey(PayType, on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'invoice'

    def __str__(self):
        return f"Factura #{self.invo_id}"


class InvoiceDetail(models.Model):
    ivo_det_id = models.AutoField(primary_key=True)
    prod_id = models.IntegerField()
    quantity_invo_det = models.IntegerField()
    invo_price_unit = models.DecimalField(max_digits=10, decimal_places=2)
    invo_det_invo = models.ForeignKey(Invoice, on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'Invoice_detail'

    def __str__(self):
        return f"Detalle de Factura #{self.ivo_det_id}"
    
    
