from django.db import models

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
        managed = True
        db_table = 'Providers'

    def __str__(self):
        return self.prov_name
    


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
    
    
