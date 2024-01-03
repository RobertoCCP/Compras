from django.db import models
from django.http import request
from django.contrib.auth.models import AbstractUser

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



class Invoice(models.Model):
    invo_id = models.CharField(max_length=16, default="new_invoice_invo_id_seq", primary_key=True)
    invo_date = models.DateField()
    user_id = models.CharField(max_length=10)
    expedition_date = models.DateField()
    invo_prov_id = models.ForeignKey(Providers, on_delete=models.CASCADE, db_column='invo_prov_id')
    invo_pay_type = models.ForeignKey(PayType, on_delete=models.CASCADE, db_column='invo_pay_type')
    
    class Meta:
        managed = False
        db_table = 'invoice'

    def _str_(self):
        return self.pay_name
    
    def _str_(self):
        return f"Invoice ID: {self.invo_id}, Date: {self.invo_date}"


class InvoiceDetail(models.Model):
    ivo_det_id = models.IntegerField(primary_key=True)
    prod_id = models.IntegerField()
    quantity_invo_det = models.IntegerField()
    invo_det_invo_id = models.ForeignKey(Invoice, on_delete=models.CASCADE, db_column='invo_det_invo_id')
    
    def __str__(self):
        return f"Invoice Detail ID: {self.ivo_det_id}, Product ID: {self.prod_id}, Quantity: {self.quantity_invo_det}"

    class Meta:
        managed = False
        db_table = "Invoice_detail"

    def str(self):
        return f"Detalle de Factura #{self.ivo_det_id}"


class Product(models.Model):
    prod_id=models.AutoField(primary_key=True)
    prod_name=models.CharField(max_length=255)
    prod_descripcion=models.CharField(max_length=300)
    prod_cost=models.DecimalField(max_digits=10, decimal_places=2)
    prod_pvp=models.DecimalField(max_digits=10, decimal_places=2)
    prod_state=models.BooleanField()
    prod_iva=models.BooleanField()
    class Meta:
        managed = False
        db_table = 'Product'

    def _str_(self):
        return f"Producto #{self.prod_id}"
    


# Define the Personal model
class Personal(models.Model):
  id = models.AutoField(primary_key=True)
  username = models.CharField(max_length=255, unique=True)
  password = models.CharField(max_length=255)
  email = models.CharField(max_length=255)

  # Define the model's Meta class
  class Meta:
    # Set the model's name
    verbose_name = 'Personal'
    # Set the model's plural name
    verbose_name_plural = 'Personales'

  # Define the model's methods
  def __str__(self):
    # Return the model's username
    return self.username